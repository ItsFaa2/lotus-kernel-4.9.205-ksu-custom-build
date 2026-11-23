	.text
	.file	"bounds.c"
	.globl	main                            // -- Begin function main
	.p2align	2
	.type	main,@function
main:                                   // @main
.Lfunc_begin0:
	.file	1 "/root/kernel-source/work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/kernel/bounds.c"
	.loc	1 16 0                          // work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/kernel/bounds.c:16:0
	.cfi_sections .debug_frame
	.cfi_startproc
// %bb.0:
	.loc	1 18 2 prologue_end             // work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/kernel/bounds.c:18:2
	//APP
	
.ascii "->NR_PAGEFLAGS 23 __NR_PAGEFLAGS"
	//NO_APP
	.loc	1 19 2                          // work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/kernel/bounds.c:19:2
	//APP
	
.ascii "->MAX_NR_ZONES 3 __MAX_NR_ZONES"
	//NO_APP
	.loc	1 21 2                          // work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/kernel/bounds.c:21:2
	//APP
	
.ascii "->NR_CPUS_BITS 3 ilog2(CONFIG_NR_CPUS)"
	//NO_APP
	.loc	1 23 2                          // work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/kernel/bounds.c:23:2
	//APP
	
.ascii "->SPINLOCK_SIZE 4 sizeof(spinlock_t)"
	//NO_APP
	.loc	1 26 2                          // work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/kernel/bounds.c:26:2
	mov	w0, wzr
	ret
.Ltmp0:
.Lfunc_end0:
	.size	main, .Lfunc_end0-main
	.cfi_endproc
                                        // -- End function
	.section	.debug_abbrev,"",@progbits
	.byte	1                               // Abbreviation Code
	.byte	17                              // DW_TAG_compile_unit
	.byte	1                               // DW_CHILDREN_yes
	.byte	37                              // DW_AT_producer
	.byte	14                              // DW_FORM_strp
	.byte	19                              // DW_AT_language
	.byte	5                               // DW_FORM_data2
	.byte	3                               // DW_AT_name
	.byte	14                              // DW_FORM_strp
	.byte	16                              // DW_AT_stmt_list
	.byte	23                              // DW_FORM_sec_offset
	.byte	27                              // DW_AT_comp_dir
	.byte	14                              // DW_FORM_strp
	.byte	17                              // DW_AT_low_pc
	.byte	1                               // DW_FORM_addr
	.byte	18                              // DW_AT_high_pc
	.byte	6                               // DW_FORM_data4
	.byte	0                               // EOM(1)
	.byte	0                               // EOM(2)
	.byte	2                               // Abbreviation Code
	.byte	46                              // DW_TAG_subprogram
	.byte	0                               // DW_CHILDREN_no
	.byte	17                              // DW_AT_low_pc
	.byte	1                               // DW_FORM_addr
	.byte	18                              // DW_AT_high_pc
	.byte	6                               // DW_FORM_data4
	.byte	64                              // DW_AT_frame_base
	.byte	24                              // DW_FORM_exprloc
	.ascii	"\227B"                         // DW_AT_GNU_all_call_sites
	.byte	25                              // DW_FORM_flag_present
	.byte	3                               // DW_AT_name
	.byte	14                              // DW_FORM_strp
	.byte	58                              // DW_AT_decl_file
	.byte	11                              // DW_FORM_data1
	.byte	59                              // DW_AT_decl_line
	.byte	11                              // DW_FORM_data1
	.byte	39                              // DW_AT_prototyped
	.byte	25                              // DW_FORM_flag_present
	.byte	73                              // DW_AT_type
	.byte	19                              // DW_FORM_ref4
	.byte	63                              // DW_AT_external
	.byte	25                              // DW_FORM_flag_present
	.byte	0                               // EOM(1)
	.byte	0                               // EOM(2)
	.byte	3                               // Abbreviation Code
	.byte	36                              // DW_TAG_base_type
	.byte	0                               // DW_CHILDREN_no
	.byte	3                               // DW_AT_name
	.byte	14                              // DW_FORM_strp
	.byte	62                              // DW_AT_encoding
	.byte	11                              // DW_FORM_data1
	.byte	11                              // DW_AT_byte_size
	.byte	11                              // DW_FORM_data1
	.byte	0                               // EOM(1)
	.byte	0                               // EOM(2)
	.byte	0                               // EOM(3)
	.section	.debug_info,"",@progbits
.Lcu_begin0:
	.word	.Ldebug_info_end0-.Ldebug_info_start0 // Length of Unit
.Ldebug_info_start0:
	.hword	4                               // DWARF version number
	.word	.debug_abbrev                   // Offset Into Abbrev. Section
	.byte	8                               // Address Size (in bytes)
	.byte	1                               // Abbrev [1] 0xb:0x40 DW_TAG_compile_unit
	.word	.Linfo_string0                  // DW_AT_producer
	.hword	1                               // DW_AT_language
	.word	.Linfo_string1                  // DW_AT_name
	.word	.Lline_table_start0             // DW_AT_stmt_list
	.word	.Linfo_string2                  // DW_AT_comp_dir
	.xword	.Lfunc_begin0                   // DW_AT_low_pc
	.word	.Lfunc_end0-.Lfunc_begin0       // DW_AT_high_pc
	.byte	2                               // Abbrev [2] 0x2a:0x19 DW_TAG_subprogram
	.xword	.Lfunc_begin0                   // DW_AT_low_pc
	.word	.Lfunc_end0-.Lfunc_begin0       // DW_AT_high_pc
	.byte	1                               // DW_AT_frame_base
	.byte	111
                                        // DW_AT_GNU_all_call_sites
	.word	.Linfo_string3                  // DW_AT_name
	.byte	1                               // DW_AT_decl_file
	.byte	15                              // DW_AT_decl_line
                                        // DW_AT_prototyped
	.word	67                              // DW_AT_type
                                        // DW_AT_external
	.byte	3                               // Abbrev [3] 0x43:0x7 DW_TAG_base_type
	.word	.Linfo_string4                  // DW_AT_name
	.byte	5                               // DW_AT_encoding
	.byte	4                               // DW_AT_byte_size
	.byte	0                               // End Of Children Mark
.Ldebug_info_end0:
	.section	.debug_str,"MS",@progbits,1
.Linfo_string0:
	.asciz	"Debian clang version 13.0.1-11+b2" // string offset=0
.Linfo_string1:
	.asciz	"/root/kernel-source/work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/kernel/bounds.c" // string offset=34
.Linfo_string2:
	.asciz	"/root/kernel-source/build/ksu-32915384-49" // string offset=162
.Linfo_string3:
	.asciz	"main"                          // string offset=204
.Linfo_string4:
	.asciz	"int"                           // string offset=209
	.ident	"Debian clang version 13.0.1-11+b2"
	.section	".note.GNU-stack","",@progbits
	.section	.debug_line,"",@progbits
.Lline_table_start0:
