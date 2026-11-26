#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FanchmWrt - Xiaomi Mi Router 3G（非 v2）去 WiFi 补丁

做两件事：
1. 从 target/linux/ramips/image/mt7621.mk 的 xiaomi_mi-router-3g 设备定义中
   移除 kmod-mt7603 / kmod-mt76x2（MT7603E 2.4G 与 MT7612E 5G 驱动）。
2. 在 target/linux/ramips/dts/mt7621_xiaomi_mi-router-3g.dts 中把 PCIe 控制器
   状态改为 disabled —— R3G 的两颗 WiFi 芯片都挂在 PCIe 上，禁用后彻底不工作。

任何一步匹配失败都会以非零状态退出，避免"看似成功、实际没改到"。
用法：python3 trim-wifi.py <源码根目录>
"""

import re
import sys
import pathlib


def fail(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def patch_device_packages(root: pathlib.Path) -> None:
    mk = root / "target" / "linux" / "ramips" / "image" / "mt7621.mk"
    if not mk.is_file():
        fail(f"找不到文件：{mk}")

    text = mk.read_text(encoding="utf-8")
    # 精确定位 xiaomi_mi-router-3g 设备定义块（不会误匹配 -v2）
    m = re.search(r"(define Device/xiaomi_mi-router-3g\n(?:.*\n)*?endef\n)", text)
    if not m:
        fail("mt7621.mk 中未找到 Device/xiaomi_mi-router-3g 定义")

    block = m.group(1)
    has_7603 = "kmod-mt7603" in block
    has_76x2 = "kmod-mt76x2" in block

    if not has_7603 and not has_76x2:
        print("INFO: DEVICE_PACKAGES 中已无无线驱动，跳过（源码可能已打过补丁）")
        return

    if not (has_7603 and has_76x2):
        fail("设备定义中的无线驱动包不完整，源码格式可能已变化，请人工检查")

    new_block = block.replace(
        "DEVICE_PACKAGES += kmod-mt7603 kmod-mt76x2 ", "DEVICE_PACKAGES += "
    )
    if new_block == block:
        fail("无法移除无线驱动包（DEVICE_PACKAGES 行格式与预期不符）")

    mk.write_text(text.replace(block, new_block, 1), encoding="utf-8")
    print("OK: 已从 xiaomi_mi-router-3g 移除 kmod-mt7603 / kmod-mt76x2")


def patch_dts(root: pathlib.Path) -> None:
    dts = (
        root
        / "target"
        / "linux"
        / "ramips"
        / "dts"
        / "mt7621_xiaomi_mi-router-3g.dts"
    )
    if not dts.is_file():
        fail(f"找不到文件：{dts}")

    text = dts.read_text(encoding="utf-8")
    old = '&pcie {\n\tstatus = "okay";\n};'
    new = '&pcie {\n\tstatus = "disabled";\n};'

    if old in text:
        dts.write_text(text.replace(old, new, 1), encoding="utf-8")
        print("OK: 已在设备树中禁用 PCIe（两颗 WiFi 芯片不再工作）")
    elif new in text:
        print("INFO: PCIe 已处于 disabled 状态，跳过")
    else:
        fail("DTS 中未找到 &pcie 的 status 定义，源码格式可能已变化，请人工检查")


def verify(root: pathlib.Path) -> None:
    mk = root / "target" / "linux" / "ramips" / "image" / "mt7621.mk"
    dts = (
        root
        / "target"
        / "linux"
        / "ramips"
        / "dts"
        / "mt7621_xiaomi_mi-router-3g.dts"
    )

    block = re.search(
        r"(define Device/xiaomi_mi-router-3g\n(?:.*\n)*?endef\n)",
        mk.read_text(encoding="utf-8"),
    )
    if not block:
        fail("校验失败：无法重新定位设备定义")
    b = block.group(1)
    if "kmod-mt7603" in b or "kmod-mt76x2" in b:
        fail("校验失败：设备定义中仍残留无线驱动包")

    if '&pcie {\n\tstatus = "disabled";\n};' not in dts.read_text(encoding="utf-8"):
        fail("校验失败：DTS 中 PCIe 未处于 disabled 状态")

    print("校验通过：无线驱动已移除，PCIe 已禁用")


def main() -> None:
    if len(sys.argv) < 2:
        fail("用法：python3 trim-wifi.py <FanchnWrt 源码根目录>")

    root = pathlib.Path(sys.argv[1]).resolve()
    if not (root / "target" / "linux" / "ramips").is_dir():
        fail(f"{root} 不像 FanchmWrt/OpenWrt 源码根目录")

    patch_device_packages(root)
    patch_dts(root)
    verify(root)


if __name__ == "__main__":
    main()