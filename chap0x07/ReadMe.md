# 移动终端应用逆向分析实验

## 实验环境

+ Android Studio 4.2.1
+ `apktool`

## 实验过程

### `smali`代码分析

1. 检出[Deliberately Vulnerable Android Hello World](https://github.com/c4pr1c3/DVAHW)最新版代码，在Android Studio中导入该项目）;

2. `Build` -> `Generate Signed APK...`，生成发布版apk，文件位于项目根目录下相对路径：`app/release/app-release.apk`；

   ![app-release.apk](images/app-release.apk.PNG)

   + 此时App运行和使用效果如下动图所示：

     ![RegisterFailed](images/RegisterFailed.gif)

3. 反编译

   ```bash
   # 在app-release.apk文件所在目录执行如下命令
   # 确认 apktool 在系统 PATH 环境变量中可找到
   apktool d app-release.apk
   ```

4. 反编译成功后，会在当前目录下生成apk文件名命名的一个独立目录。

   ![Decompile](images/Decompile.PNG)

   + 反汇编出来的`smali`代码位于apktool输出目录下的 **smali** 子目录，源代码目录中的 **res** 目录也位于输出目录的一级子目录下。

     ![SmaliAndRes](images/SmaliAndRes.PNG)

5. 注意到其中的提示消息内容为：**注册失败**。依据此**关键特征**，在反汇编输出目录下进行**关键字查找**，可以在 `res/values/strings.xml` 中找到该关键字的注册变量名为`register_failed`。

   ![GrepRegisterFailed.PNG](images/GrepRegisterFailed.PNG)

6. 用文本编辑器打开 `res/values/strings.xml` 查看会在上述代码行下一行发现：

   ```xml
   <string name="register_ok">注册成功</string>
   ```

   ![FindRegisterOk](images/FindRegisterOk.PNG)

7. 继续在反汇编输出目录下进行**关键字查找**：`register_ok`，可以发现

   ```smali
   ./smali/cn/edu/cuc/misdemo/R$string.smali:.field public static final register_ok:I = 0x7f060027
   ```

   ![GrepRegisterOk](images/GrepRegisterOk.PNG)

8. 现在，我们有了`register_ok`的资源唯一标识符：`0x7f0b0025`，使用该唯一标识符进行关键字查找，我们可以定位到这一段代码：

   ```bash
   ./smali/cn/edu/cuc/misdemo/DisplayMessageActivity.smali:    const v0, 0x7f0b0025
   ```

   ![FindDisplayPage.PNG](images/FindDisplayPage.PNG)

9. 用文本编辑器打开上述`DisplayMessageActivity.smali`，定位到包含该资源唯一标识符所在的代码行。同时，在Android Studio中打开`DisplayMessageActivity.java`源代码，定位到包含`textView.setText(getString(R.string.register_ok));`的代码行。

   ​![contrast.PNG](images/contrast.PNG)

10. 根据源代码行号和smali代码中的`.line 39`，我们可以找到Android源代码中的Java代码和Smali代码之间的对应“翻译”关系。上述smali代码注释说明如下：

    ```bash
    # 当前smali代码对应源代码的行号
    .line 39

    # 将 0x7f060027 赋值给寄存器v6
    const v0, 0x7f0b0025

    # invoke-virtual 是调用实例的虚方法（该方法不能是 private、static 或 final，也不能是构造函数）
    # 在非static方法中，p0代指this
    # 此处的实例对象是 cn.edu.cuc.misdemo.DisplayMessageActivity
    # Lcn/edu/cuc/misdemo/DisplayMessageActivity; 表示DisplayMessageActivity这个对象实例 getString是具体方法名
    # I表示参数是int类型
    # Ljava/lang/String; 表示 Java内置的String类型对象
    # 整个这一行smali代码表示的就是 调用 cn.edu.cuc.misdemo.DisplayMessageActivity对象的getString方法，传入一个整型参数值，得到String类型返回结果
    invoke-virtual {p0, v0}, Lcn/edu/cuc/misdemo/DisplayMessageActivity;->getString(I)Ljava/lang/String;

    # 将最新的 invoke-kind 的对象结果移到指定的寄存器中。该指令必须紧跟在（对象）结果不会被忽略的 invoke-kind 或 filled-new-array 之后执行，否则无效。
    # 其中 kind 典型取值如virtual、super、direct、static、interface等，详见Android开源官网的 'Dalvik 字节码' 说明文档
    move-result-object v0

    # 此处的v1赋值发生在 .line 37，需要注意的是这里的v1是一个局部变量（用v表示），并不是参数寄存器（用p表示）。
    # 当前initView()方法通过 .locals 定义了8个本地寄存器，用于保存局部变量，如下2行代码所示：
    # .method private initView()V
    #    .locals 8
    # V 表示 setText 的返回结果是 void 类型
    invoke-virtual {v1, v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    ```

11. 搞懂了上述smali代码的含义之后，我们破解这个 **简单注册小程序** 的思路可以归纳如下：

    + 改变原来的注册码相等条件判断语句，对布尔类型返回结果直接取反，达到：只要我们没有输入正确的验证码，就能通过验证的“破解”效果；

      + 将 `if-eqz` 修改为 `if-nez`

       ![Change_eqz.PNG](images/Change_eqz.PNG)

    + 在执行注册码相等条件判断语句之前，打印出用于和用户输入的注册码进行比较的“正确验证码”变量的值，借助`adb logcat`直接“偷窥”到正确的验证码；

      + 增加2行打印语句:

        ![AddCode](images/AddCode.PNG)

上述2种思路都需要直接修改smali代码，然后对反汇编目录进行**重打包**和**重签名**。

### 重打包

```bash
apktool b app-release
```

![Repackaging](images/Repackaging.PNG)

### 重签名

```bash
cd app-release/dist/
<Android SDK Path>/build-tools/<valid version code>/apksigner sign --min-sdk-version 19 --ks <path to release.keystore.jks> --out app-release-signed.apk app-release.apk
```

![ReSign](images/ReSign.PNG)

### 安装

![Install](images/Install.PNG)

### 破解效果展示

直接通过“取反”注册码判断逻辑修改后的APK运行和使用效果如下动图所示：

![CrackResult1](images/CrackResult1.gif)

通过**插桩**打印语句方式实现的直接“偷窥”正确注册码方法修改后的APK运行和使用效果如下动图所示：

![CrackResult2](images/CrackResult2.gif)

## 实验问题解答

+ [x] 使用apktool反汇编上一章实验中我们开发的Hello World v2版程序，对比Java源代码和smali汇编代码之间的一一对应关系。

  + 上述`smali代码分析`第10步为`DVAHW`的Java源代码和smali汇编代码之间的一一对应关系，Hello World v2版与此类似。

+ [x] 对Hello World v2版程序生成的APK文件进行程序图标替换，并进行重打包，要求可以安装到一台未安装过Hello World v2版程序的Android模拟器中。

  + 修改`..\res\mipmap-xxxhdpi\ic_launcher.png`目录下的图标文件后重打包、重签名、安装

  + 图标替换结果：

    ![IconReplacement](images/IconReplacement.PNG)

+ [x] 尝试安装重打包版Hello World v2到一台已经安装过原版Hello World v2程序的模拟器中，观察出错信息并解释原因。

  ​![InstallError](images/InstallError.PNG)

  + 原因：签名和之前的版本不匹配。卸载后再安装就OK了。

+ [x] 去掉Hello World v2版程序中DisplayMessageActivity.java代码中的那2行日志打印语句后编译出一个新的apk文件，假设文件名是：misdemo-v3.apk，尝试使用课件中介绍的几种软件逆向分析方法来破解我们的认证算法。

  见`smali代码分析`第11步。与此类似。

## 遇到的问题

+ 重签名后安装应用报错

  ![error](images/error.PNG)

  + 根据报错信息提示，Android R+不在允许app压缩`resource.asrc`。没找到合适的解决方法，于是新建了一个`version 29`的模拟器完成了次子实验。

## 参考资料

+ [第七章 移动终端应用逆向分析](https://c4pr1c3.github.io/cuc-mis/chap0x07/exp.html)
+ [2021 Android APK反编译 apktool使用教程](https://blog.csdn.net/ysc123shift/article/details/52985435)
+ [Android打包报错：Lint found fatal errors while assembling a release target.](https://blog.csdn.net/aiynmimi/article/details/89401239)
