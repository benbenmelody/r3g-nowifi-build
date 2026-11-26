# 小米 R3G（非 v2）FanchmWrt 无 WiFi 固件 — 云编译包

用 GitHub Actions 从 [fanchmwrt/fanchmwrt](https://github.com/fanchmwrt/fanchmwrt) 源码编译
**Xiaomi Mi Router 3G（非 v2，NAND 128MB）** 的固件，并彻底裁剪 WiFi 功能。

- 源码分支：`fanchmwrt-25.12.6`
- 目标设备：`ramips / mt7621 / xiaomi_mi-router-3g`
- 编译环境：Ubuntu 22.04（GitHub 托管运行器，无需本机装 Linux）
- 预计耗时：约 60~100 分钟/次

---

## 一、这个包做了什么

| 改动点 | 文件 | 说明 |
|---|---|---|
| 移除无线驱动 | `target/linux/ramips/image/mt7621.mk` | 从 `xiaomi_mi-router-3g` 的 `DEVICE_PACKAGES` 去掉 `kmod-mt7603`、`kmod-mt76x2`（MT7603E 2.4G + MT7612E 5G） |
| 禁用 PCIe | `target/linux/ramips/dts/mt7621_xiaomi_mi-router-3g.dts` | `&pcie` 由 `okay` 改为 `disabled`，两颗 WiFi 芯片不枚举、不工作，更省电 |
| 配置双保险 | `configs/r3g-nowifi.config` | 不选无线驱动、`wpad-basic-mbedtls`、无线管理界面 `luci-app-fwx-wireless` |

> 说明：FanchmWrt 默认包集里的 `fwxd` 只依赖用户态 `rpcd-mod-iwinfo`，不会把无线驱动拉回来；
> 裁剪只影响 WiFi，PPPoE、防火墙、DNS、USB、WireGuard、ksmbd 等有线功能全部保留。

目录结构：

```
R3G-NoWiFi-Firmware/
├── .github/workflows/build-r3g-nowifi.yml   # GitHub Actions 编译流程
├── configs/r3g-nowifi.config                # 固件配置
├── scripts/trim-wifi.py                     # 去 WiFi 补丁脚本（编译时自动执行）
└── README.md                                # 本说明
```

---

## 二、把构建包上传到 GitHub（一次性，约 3 分钟）

1. 打开 <https://github.com>，登录（没有账号先免费注册）。
2. 右上角 **+** → **New repository**。
3. 填写：
   - **Repository name**：`r3g-nowifi-build`（任意名字均可）
   - 可见性：**Private** 或 **Public** 都行（Public 的 Actions 分钟数不限；Private 每月有 2000 分钟免费额度，够编译 20 次以上）
   - **不要**勾选 "Add a README file" 等初始化选项
4. 点 **Create repository**。
5. 在新仓库页面点 **uploading an existing file**（或 **Add file → Upload files**）。
6. 打开本文件夹 `R3G-NoWiFi-Firmware`，把里面的 **`.github`、`configs`、`scripts`、`README.md`** 全部选中，拖进浏览器上传区域。
   - 网页上传支持整个文件夹；`.github` 是普通文件夹，Windows 里可正常看到。
   - 如果拖拽文件夹不方便，也可以用 GitHub Desktop 或 git 命令行推送。
7. 下方点 **Commit changes**。

> 上传后仓库根目录应能看到 `.github`、`configs`、`scripts`、`README.md` 四项。

---

## 三、触发编译（约 1~1.5 小时）

1. 进入仓库顶部 **Actions** 标签。
2. 若提示启用工作流，点 **I understand my workflows, go ahead and enable them**。
3. 左侧选择 **Build FanchmWrt R3G (No WiFi)**。
4. 右侧点 **Run workflow** → 分支选 `main` → 绿色 **Run workflow**。
5. 刷新页面，点进正在运行的记录，可实时查看日志。各步骤含义：
   - `释放磁盘空间`：清理运行器，腾出约 30GB
   - `克隆 FanchmWrt 源码`：拉取 `fanchmwrt-25.12.6`
   - `应用去 WiFi 补丁`：执行 `scripts/trim-wifi.py`，失败会立即停止
   - `生成配置并校验`：若发现无线驱动仍为 `=y`，直接报错终止（不会白编一小时）
   - `编译固件`：全量源码编译
6. 完成后有两种下载方式：
   - **Artifacts**：该次运行页面底部 `r3g-nowifi-firmware-编号`
   - **Releases**：仓库右侧 Releases 中自动生成的 `r3g-nowifi-编号`

产物一般为：

```
openwrt-ramips-mt7621-xiaomi_mi-router-3g-squashfs-sysupgrade.bin   ← 刷机用这个
openwrt-ramips-mt7621-xiaomi_mi-router-3g-squashfs-kernel1.bin      ← Uboot/opboot 双分区刷写用
openwrt-ramips-mt7621-xiaomi_mi-router-3g-squashfs-rootfs0.bin      ← Uboot/opboot 双分区刷写用
sha256sums
build.config
```

> R3G 为 NAND 分离布局，标准产物是上表三个镜像；若日志里另有 `initramfs-kernel.bin`，可用于内存救援引导。
```

> 文件名必须含 `xiaomi_mi-router-3g` 且**不含** `-v2`，v2 固件与本机不通用。

---

## 四、刷机（现有 OpenWrt → 本固件）

> 刷机有断电变砖风险，请接有线网、用稳压电源，全程勿断电。

1. 下载并解压 Artifacts，记录 `sysupgrade.bin` 的 SHA256：
   ```powershell
   Get-FileHash .\openwrt-ramips-mt7621-xiaomi_mi-router-3g-squashfs-sysupgrade.bin -Algorithm SHA256
   ```
   与 `sha256sums` 对照一致再刷。
2. 记下现有网络配置（宽带账号/密码、LAN 网段、静态路由等），刷完后需要重配。
3. 打开 R3G 的 LuCI → **系统 → 备份/升级 → 刷写新的固件**：
   - 选择 `...squashfs-sysupgrade.bin`
   - **不要勾选"保留配置"**（跨固件品牌，配置结构不同，保留容易出问题）
   - 点"刷写固件"，确认
4. 或 SSH 刷写：
   ```bash
   scp openwrt-ramips-mt7621-xiaomi_mi-router-3g-squashfs-sysupgrade.bin root@192.168.1.1:/tmp/
   ssh root@192.168.1.1 "sysupgrade -n /tmp/openwrt-ramips-mt7621-xiaomi_mi-router-3g-squashfs-sysupgrade.bin"
   ```
   `-n` 表示不保留配置。
5. 约 3~5 分钟后设备重启完成。默认地址 `192.168.1.1`，主机名 `FanchmWrt`；首次登录无密码，按提示设置。
6. 重新配置 WAN（PPPoE 账号密码）、LAN、DHCP 等；默认时区为 `Asia/Hong Kong`，建议在 **系统 → 系统** 中改为 `Asia/Shanghai`（两者同为 UTC+8，不影响计时）。

> 若设备当前是小米原厂固件：需先按 R3G 教程刷入 Breed/opboot 或 OpenWrt initramfs，再刷本固件；
> 本包假设设备已经在跑 OpenWrt。

---

## 五、验证 WiFi 确实被裁掉

SSH 登录后执行：

```bash
ls /sys/class/ieee80211/          # 应为空或目录不存在
iwinfo                             # 应无任何无线设备输出
dmesg | grep -iE 'pcie|mt76'      # 应无 PCIe 枚举、无 mt76 驱动加载
```

LuCI 中也不会出现"无线"相关菜单（`luci-app-fwx-wireless` 已裁掉）。

---

## 六、常见问题

| 现象 | 处理 |
|---|---|
| Actions 页面没有工作流 | 确认 `.github/workflows/build-r3g-nowifi.yml` 已上传，且路径大小写正确 |
| Release 步骤报权限错误 | 仓库 **Settings → Actions → General → Workflow permissions** 选 **Read and write permissions**，再重跑；Artifacts 不受影响 |
| 编译在 `生成配置并校验` 失败 | 说明补丁未生效或源码格式变化，下载 `build-log` 查看；把日志发我即可 |
| 编译在 `编译固件` 失败 | 下载 `build-log` artifact，搜索 `Error`；多为上游源码临时问题，隔天重跑或换 `fanchmwrt-24.10.4` 分支 |
| 想换源码版本 | 改 workflow 顶部 `SOURCE_BRANCH`（可选 `fanchmwrt-25.12.4`、`fanchmwrt-24.10.4`） |
| 想恢复 WiFi | 删除 workflow 中"应用去 WiFi 补丁"步骤，并删掉 config 中 4 行 `is not set` |
| 私有仓库分钟数 | 每次约 60~100 分钟；Public 仓库不计分钟数 |

---

## 七、安全与来源

- 源码：<https://github.com/fanchmwrt/fanchmwrt>（GPL-2.0）
- 本包只修改设备定义、设备树与编译配置，未改动任何业务代码
- 编译全程在 GitHub 官方运行器上完成，产物可用 `sha256sums` 校验

> AI生成
