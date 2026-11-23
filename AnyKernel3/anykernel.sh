### AnyKernel3 - Redmi 6A / MT6765
### KernelSU v0.9.2
### Kernel-only replacement
### Stock ramdisk + DTB + boot metadata preserved

properties() { '
kernel.string=LotusKernel-OSS + KernelSU v0.9.2
do.devicecheck=0
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=0
device.name1=
device.name2=
device.name3=
device.name4=
device.name5=
supported.versions=
supported.patchlevels=
supported.vendorpatchlevels=
'; }

# Boot partition
BLOCK=/dev/block/by-name/boot;
IS_SLOT_DEVICE=0;

# Preserve the original ramdisk compression detected by AK3.
RAMDISK_COMPRESSION=auto;

# Do not modify AVB/vbmeta.
PATCH_VBMETA_FLAG=auto;

# Load AnyKernel3 core.
. tools/ak3-core.sh;

# Unpack current boot image.
# This preserves ramdisk, DTB, kernel_dtb and metadata.
dump_boot;

# No ramdisk modifications.
# Kernel file "Image" is supplied by the package itself.

# Repack and write boot image.
write_boot;
