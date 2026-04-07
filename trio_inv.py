from ctypes import *


# ------------------------------------------------------------------
# [6] 주식 현재가 조회 (IVWUTKMST04)
# ------------------------------------------------------------------

# 입력 구조체 (요청용)
# 1. 기본입력
class TIVWUTKMST04In(Structure):
    _pack_ = 1
    _fields_ = [
        ("form_lang", c_char * 1),      ("_form_lang", c_char * 1),
        ("shrn_iscd", c_char * 6),      ("_shrn_iscd", c_char * 1)
    ]

# 2. 종목마스타기본자료
class TIVWUTKMST04Out1(Structure):
    _pack_ = 1
    _fields_ = [
        ("shrn_iscd", c_char * 6),          ("_shrn_iscd", c_char * 1),
        ("hts_isnm", c_char * 41),          ("_hts_isnm", c_char * 1),
        ("stck_prpr", c_char * 10),         ("_stck_prpr", c_char * 1),
        ("prdy_vrss_sign", c_char * 1),     ("_prdy_vrss_sign", c_char * 1),
        ("prdy_vrss", c_char * 10),         ("_prdy_vrss", c_char * 1),
        ("prdy_ctrt", c_char * 5),          ("_prdy_ctrt", c_char * 1),
        ("askp", c_char * 10),              ("_askp", c_char * 1),
        ("bidp", c_char * 10),              ("_bidp", c_char * 1),
        ("acml_vol", c_char * 12),          ("_acml_vol", c_char * 1),
        ("vol_rate", c_char * 6),           ("_vol_rate", c_char * 1),
        ("move_rate", c_char * 6),          ("_move_rate", c_char * 1),
        ("acml_tr_pbmn", c_char * 18),      ("_acml_tr_pbmn", c_char * 1),
        ("stck_mxpr", c_char * 10),         ("_stck_mxpr", c_char * 1),
        ("stck_hgpr", c_char * 10),         ("_stck_hgpr", c_char * 1),
        ("stck_oprc", c_char * 10),         ("_stck_oprc", c_char * 1),
        ("stck_oprc_sign", c_char * 1),     ("_stck_oprc_sign", c_char * 1),
        ("stck_oprc_vrss", c_char * 10),    ("_stck_oprc_vrss", c_char * 1),
        ("stck_lwpr", c_char * 10),         ("_stck_lwpr", c_char * 1),
        ("stck_llam", c_char * 10),         ("_stck_llam", c_char * 1),
        ("hoga_bsop_hour", c_char * 8),     ("_hoga_bsop_hour", c_char * 1),
        
        # 매도호가 1~10
        ("askp1", c_char * 10),             ("_askp1", c_char * 1),
        ("askp2", c_char * 10),             ("_askp2", c_char * 1),
        ("askp3", c_char * 10),             ("_askp3", c_char * 1),
        ("askp4", c_char * 10),             ("_askp4", c_char * 1),
        ("askp5", c_char * 10),             ("_askp5", c_char * 1),
        ("askp6", c_char * 10),             ("_askp6", c_char * 1),
        ("askp7", c_char * 10),             ("_askp7", c_char * 1),
        ("askp8", c_char * 10),             ("_askp8", c_char * 1),
        ("askp9", c_char * 10),             ("_askp9", c_char * 1),
        ("askp10", c_char * 10),            ("_askp10", c_char * 1),
        
        # 매수호가 1~10
        ("bidp1", c_char * 10),             ("_bidp1", c_char * 1),
        ("bidp2", c_char * 10),             ("_bidp2", c_char * 1),
        ("bidp3", c_char * 10),             ("_bidp3", c_char * 1),
        ("bidp4", c_char * 10),             ("_bidp4", c_char * 1),
        ("bidp5", c_char * 10),             ("_bidp5", c_char * 1),
        ("bidp6", c_char * 10),             ("_bidp6", c_char * 1),
        ("bidp7", c_char * 10),             ("_bidp7", c_char * 1),
        ("bidp8", c_char * 10),             ("_bidp8", c_char * 1),
        ("bidp9", c_char * 10),             ("_bidp9", c_char * 1),
        ("bidp10", c_char * 10),            ("_bidp10", c_char * 1),
        
        # 매도호가잔량 1~10
        ("askp_rsqn1", c_char * 12),        ("_askp_rsqn1", c_char * 1),
        ("askp_rsqn2", c_char * 12),        ("_askp_rsqn2", c_char * 1),
        ("askp_rsqn3", c_char * 12),        ("_askp_rsqn3", c_char * 1),
        ("askp_rsqn4", c_char * 12),        ("_askp_rsqn4", c_char * 1),
        ("askp_rsqn5", c_char * 12),        ("_askp_rsqn5", c_char * 1),
        ("askp_rsqn6", c_char * 12),        ("_askp_rsqn6", c_char * 1),
        ("askp_rsqn7", c_char * 12),        ("_askp_rsqn7", c_char * 1),
        ("askp_rsqn8", c_char * 12),        ("_askp_rsqn8", c_char * 1),
        ("askp_rsqn9", c_char * 12),        ("_askp_rsqn9", c_char * 1),
        ("askp_rsqn10", c_char * 12),       ("_askp_rsqn10", c_char * 1),
        
        # 매수호가잔량 1~10
        ("bidp_rsqn1", c_char * 12),        ("_bidp_rsqn1", c_char * 1),
        ("bidp_rsqn2", c_char * 12),        ("_bidp_rsqn2", c_char * 1),
        ("bidp_rsqn3", c_char * 12),        ("_bidp_rsqn3", c_char * 1),
        ("bidp_rsqn4", c_char * 12),        ("_bidp_rsqn4", c_char * 1),
        ("bidp_rsqn5", c_char * 12),        ("_bidp_rsqn5", c_char * 1),
        ("bidp_rsqn6", c_char * 12),        ("_bidp_rsqn6", c_char * 1),
        ("bidp_rsqn7", c_char * 12),        ("_bidp_rsqn7", c_char * 1),
        ("bidp_rsqn8", c_char * 12),        ("_bidp_rsqn8", c_char * 1),
        ("bidp_rsqn9", c_char * 12),        ("_bidp_rsqn9", c_char * 1),
        ("bidp_rsqn10", c_char * 12),       ("_bidp_rsqn10", c_char * 1),
        
        ("total_askp_rsqn", c_char * 12),   ("_total_askp_rsqn", c_char * 1),
        ("total_bidp_rsqn", c_char * 12),   ("_total_bidp_rsqn", c_char * 1),
        ("ovtm_askp_rsqn", c_char * 12),    ("_ovtm_askp_rsqn", c_char * 1),
        ("ovtm_bidp_rsqn", c_char * 12),    ("_ovtm_bidp_rsqn", c_char * 1),
        ("pvt_scnd_dmrs", c_char * 10),     ("_pvt_scnd_dmrs", c_char * 1),
        ("pvt_frst_dmrs", c_char * 10),     ("_pvt_frst_dmrs", c_char * 1),
        ("pvt_pont_val", c_char * 10),      ("_pvt_pont_val", c_char * 1),
        ("pvt_frst_dmsp", c_char * 10),     ("_pvt_frst_dmsp", c_char * 1),
        ("pvt_scnd_dmsp", c_char * 10),     ("_pvt_scnd_dmsp", c_char * 1),
        ("mrkt_div_isnm", c_char * 6),      ("_mrkt_div_isnm", c_char * 1),
        ("bstp_kor_isnm", c_char * 40),     ("_bstp_kor_isnm", c_char * 1),
        ("bstp_cls_code", c_char * 6),      ("_bstp_cls_code", c_char * 1),
        ("avls_scal_isnm", c_char * 6),     ("_avls_scal_isnm", c_char * 1),
        ("stac_month", c_char * 16),        ("_stac_month", c_char * 1),
        ("marcket1z16", c_char * 16),       ("_marcket1z16", c_char * 1),
        ("marcket2z16", c_char * 16),       ("_marcket2z16", c_char * 1),
        ("marcket3z16", c_char * 16),       ("_marcket3z16", c_char * 1),
        ("marcket4z16", c_char * 16),       ("_marcket4z16", c_char * 1),
        ("marcket5z16", c_char * 16),       ("_marcket5z16", c_char * 1),
        ("marcket6z16", c_char * 16),       ("_marcket6z16", c_char * 1),
        ("cb_text", c_char * 6),            ("_cb_text", c_char * 1),
        ("stck_fcam", c_char * 10),         ("_stck_fcam", c_char * 1),
        ("prdy_clpr_title", c_char * 12),   ("_prdy_clpr_title", c_char * 1),
        ("stck_prdy_clpr", c_char * 10),    ("_stck_prdy_clpr", c_char * 1),
        ("stck_sspr", c_char * 10),         ("_stck_sspr", c_char * 1),
        ("gongpricez7", c_char * 7),        ("_gongpricez7", c_char * 1),
        ("d5_hgpr", c_char * 10),           ("_d5_hgpr", c_char * 1),
        ("d5_lwpr", c_char * 10),           ("_d5_lwpr", c_char * 1),
        ("d20_hgpr", c_char * 10),          ("_d20_hgpr", c_char * 1),
        ("d20_lwpr", c_char * 10),          ("_d20_lwpr", c_char * 1),
        ("w52_hgpr", c_char * 10),          ("_w52_hgpr", c_char * 1),
        ("w52_hgpr_date", c_char * 4),      ("_w52_hgpr_date", c_char * 1),
        ("w52_lwpr", c_char * 10),          ("_w52_lwpr", c_char * 1),
        ("w52_lwpr_date", c_char * 4),      ("_w52_lwpr_date", c_char * 1),
        ("move_stcn", c_char * 12),         ("_move_stcn", c_char * 1),
        ("lstn_stcn_unit3", c_char * 12),   ("_lstn_stcn_unit3", c_char * 1),
        ("hts_avls", c_char * 12),          ("_hts_avls", c_char * 1),
        ("memb_bsop_hour", c_char * 5),     ("_memb_bsop_hour", c_char * 1),
        
        # 거래원 1~5 (매도/매수/수량)
        ("seln_mbcr_name1", c_char * 6),    ("_seln_mbcr_name1", c_char * 1),
        ("shnu_mbcr_name1", c_char * 6),    ("_shnu_mbcr_name1", c_char * 1),
        ("seln_qty1", c_char * 12),         ("_seln_qty1", c_char * 1),
        ("shnu_qty1", c_char * 12),         ("_shnu_qty1", c_char * 1),
        ("seln_mbcr_name2", c_char * 6),    ("_seln_mbcr_name2", c_char * 1),
        ("shnu_mbcr_name2", c_char * 6),    ("_shnu_mbcr_name2", c_char * 1),
        ("seln_qty2", c_char * 12),         ("_seln_qty2", c_char * 1),
        ("shnu_qty2", c_char * 12),         ("_shnu_qty2", c_char * 1),
        ("seln_mbcr_name3", c_char * 6),    ("_seln_mbcr_name3", c_char * 1),
        ("shnu_mbcr_name3", c_char * 6),    ("_shnu_mbcr_name3", c_char * 1),
        ("seln_qty3", c_char * 12),         ("_seln_qty3", c_char * 1),
        ("shnu_qty3", c_char * 12),         ("_shnu_qty3", c_char * 1),
        ("seln_mbcr_name4", c_char * 6),    ("_seln_mbcr_name4", c_char * 1),
        ("shnu_mbcr_name4", c_char * 6),    ("_shnu_mbcr_name4", c_char * 1),
        ("seln_qty4", c_char * 12),         ("_seln_qty4", c_char * 1),
        ("shnu_qty4", c_char * 12),         ("_shnu_qty4", c_char * 1),
        ("seln_mbcr_name5", c_char * 6),    ("_seln_mbcr_name5", c_char * 1),
        ("shnu_mbcr_name5", c_char * 6),    ("_shnu_mbcr_name5", c_char * 1),
        ("seln_qty5", c_char * 12),         ("_seln_qty5", c_char * 1),
        ("shnu_qty5", c_char * 12),         ("_shnu_qty5", c_char * 1),
        
        ("glob_seln_qty", c_char * 12),     ("_glob_seln_qty", c_char * 1),
        ("glob_shnu_qty", c_char * 12),     ("_glob_shnu_qty", c_char * 1),
        ("for_hour", c_char * 6),           ("_for_hour", c_char * 1),
        ("for_rate", c_char * 5),           ("_for_rate", c_char * 1),
        ("crdt_stlm_date", c_char * 4),     ("_crdt_stlm_date", c_char * 1),
        ("crdt_rmnd_rate", c_char * 5),     ("_crdt_rmnd_rate", c_char * 1),
        ("yu_date", c_char * 4),            ("_yu_date", c_char * 1),
        ("mu_date", c_char * 4),            ("_mu_date", c_char * 1),
        ("yu_rate", c_char * 5),            ("_yu_rate", c_char * 1),
        ("mu_rate", c_char * 5),            ("_mu_rate", c_char * 1),
        ("frgn_ntby_vol", c_char * 10),     ("_frgn_ntby_vol", c_char * 1),
        ("jasa", c_char * 1),               ("_jasa", c_char * 1),
        ("stck_lstn_date", c_char * 8),     ("_stck_lstn_date", c_char * 1),
        ("dae_rate", c_char * 5),           ("_dae_rate", c_char * 1),
        ("dae_date", c_char * 6),           ("_dae_date", c_char * 1),
        ("filler", c_char * 1),             ("_filler", c_char * 1),
        ("deposit_gb", c_char * 1),         ("_deposit_gb", c_char * 1),
        ("cpfn", c_char * 12),              ("_cpfn", c_char * 1),
        ("total_seln_qty", c_char * 12),    ("_total_seln_qty", c_char * 1),
        ("total_shnu_qty", c_char * 12),    ("_total_shnu_qty", c_char * 1),
        ("detour_gb", c_char * 1),          ("_detour_gb", c_char * 1),
        ("scrt_grp_isnm", c_char * 6),      ("_scrt_grp_isnm", c_char * 1),
        ("crdt_deal_date", c_char * 4),     ("_crdt_deal_date", c_char * 1),
        ("crdt_loan_gvrt", c_char * 5),     ("_crdt_loan_gvrt", c_char * 1),
        ("per", c_char * 5),                ("_per", c_char * 1),
        ("hando_gb", c_char * 1),           ("_hando_gb", c_char * 1),
        ("wghn_avrg_prc", c_char * 10),     ("_wghn_avrg_prc", c_char * 1),
        ("lstn_stcn_unit0", c_char * 12),   ("_lstn_stcn_unit0", c_char * 1),
        ("add_lstn_stcn", c_char * 12),     ("_add_lstn_stcn", c_char * 1),
        ("gicomment", c_char * 100),        ("_gicomment", c_char * 1),
        ("prdy_vol", c_char * 12),          ("_prdy_vol", c_char * 1),
        ("pre_prdy_sign", c_char * 1),      ("_pre_prdy_sign", c_char * 1),
        ("pre_prdy_vrss", c_char * 10),     ("_pre_prdy_vrss", c_char * 1),
        ("stck_dryy_hgpr", c_char * 10),    ("_stck_dryy_hgpr", c_char * 1),
        ("dryy_hgpr_date", c_char * 4),     ("_dryy_hgpr_date", c_char * 1),
        ("stck_dryy_lwpr", c_char * 10),    ("_stck_dryy_lwpr", c_char * 1),
        ("dryy_lwpr_date", c_char * 4),     ("_dryy_lwpr_date", c_char * 1),
        ("frgn_hldn_qty", c_char * 15),     ("_frgn_hldn_qty", c_char * 1),
        ("issu_limt_rate", c_char * 5),     ("_issu_limt_rate", c_char * 1),
        ("frml_mrkt_unit", c_char * 5),     ("_frml_mrkt_unit", c_char * 1),
        ("comp_cls_code", c_char * 1),      ("_comp_cls_code", c_char * 1),
        ("largem_gb", c_char * 1),          ("_largem_gb", c_char * 1),
        ("pbr", c_char * 5),                ("_pbr", c_char * 1),
        ("dmrs_val", c_char * 7),           ("_dmrs_val", c_char * 1),
        ("dmsp_val", c_char * 7),           ("_dmsp_val", c_char * 1),
        ("prdy_tr_pbmn", c_char * 12),      ("_prdy_tr_pbmn", c_char * 1),
        ("vi_antc_sdpr", c_char * 10),      ("_vi_antc_sdpr", c_char * 1),
        ("vi_antc_mxpr", c_char * 10),      ("_vi_antc_mxpr", c_char * 1),
        ("vi_antc_llam", c_char * 10),      ("_vi_antc_llam", c_char * 1),
        ("invt_epmd_yn", c_char * 1),       ("_invt_epmd_yn", c_char * 1),
        ("uplm_qty", c_char * 12),          ("_uplm_qty", c_char * 1),
        ("short_over_code", c_char * 1),    ("_short_over_code", c_char * 1),
        ("mrkt_alrm_code", c_char * 1),     ("_mrkt_alrm_code", c_char * 1),
        ("sltr_yn", c_char * 1),            ("_sltr_yn", c_char * 1),
        ("crd_rt_grd_nm", c_char * 6),      ("_crd_rt_grd_nm", c_char * 1),
        ("mid_prc", c_char * 10),           ("_mid_prc", c_char * 1),
        ("midp_total_askp_rsqn", c_char * 12),  ("_midp_total_askp_rsqn", c_char * 1),
        ("midp_total_bidp_rsqn", c_char * 12),  ("_midp_total_bidp_rsqn", c_char * 1),
        ("nxt_mid_prc", c_char * 10),           ("_nxt_mid_prc", c_char * 1),
        ("nxt_midp_total_askp_rsqn", c_char * 12), ("_nxt_midp_total_askp_rsqn", c_char * 1),
        ("nxt_midp_total_bidp_rsqn", c_char * 12), ("_nxt_midp_total_bidp_rsqn", c_char * 1)
    ]

# 3. 변동거래량자료
class TIVWUTKMST04Out2(Structure):
    _pack_ = 1
    _fields_ = [
        ("bsop_hour", c_char * 8),          ("_bsop_hour", c_char * 1),
        ("stck_prpr", c_char * 10),         ("_stck_prpr", c_char * 1),
        ("prdy_vrss_sign", c_char * 1),     ("_prdy_vrss_sign", c_char * 1),
        ("prdy_vrss", c_char * 10),         ("_prdy_vrss", c_char * 1),
        ("askp", c_char * 10),              ("_askp", c_char * 1),
        ("bidp", c_char * 10),              ("_bidp", c_char * 1),
        ("cntg_vol", c_char * 12),          ("_cntg_vol", c_char * 1),
        ("acml_vol", c_char * 12),          ("_acml_vol", c_char * 1)
    ]

# 4. 종목지표
class TIVWUTKMST04Out3(Structure):
    _pack_ = 1
    _fields_ = [
        ("cncc_aspr_code", c_char * 1),     ("_cncc_aspr_code", c_char * 1),
        ("antc_cnpr", c_char * 10),         ("_antc_cnpr", c_char * 1),
        ("antc_cntg_sign", c_char * 1),     ("_antc_cntg_sign", c_char * 1),
        ("antc_cntg_vrss", c_char * 10),    ("_antc_cntg_vrss", c_char * 1),
        ("antc_prdy_ctrt", c_char * 5),     ("_antc_prdy_ctrt", c_char * 1),
        ("antc_vol", c_char * 12),          ("_antc_vol", c_char * 1),
        ("chkdataz1", c_char * 1),          ("_chkdataz1", c_char * 1),
        ("ovtm_untp_prpr", c_char * 10),    ("_ovtm_untp_prpr", c_char * 1),
        ("ovtm_untp_sign", c_char * 1),     ("_ovtm_untp_sign", c_char * 1),
        ("ovtm_untp_vrss", c_char * 10),    ("_ovtm_untp_vrss", c_char * 1),
        ("ovtm_untp_ctrt", c_char * 5),     ("_ovtm_untp_ctrt", c_char * 1),
        ("ovtm_untp_vol", c_char * 12),     ("_ovtm_untp_vol", c_char * 1),
        ("ovtm_antc_sign", c_char * 1),     ("_ovtm_antc_sign", c_char * 1),
        ("ovtm_antc_vrss", c_char * 10),    ("_ovtm_antc_vrss", c_char * 1),
        ("ovtm_antc_ctrt", c_char * 5),     ("_ovtm_antc_ctrt", c_char * 1),
        ("scoring", c_char * 6),            ("_scoring", c_char * 1),
        ("vi_type_code", c_char * 1),       ("_vi_type_code", c_char * 1)
    ]

# 5. 전체 구조체
class TIVWUTKMST04(Structure):
    _pack_ = 1
    _fields_ = [
        ("IVWUTKMST04in", TIVWUTKMST04In),
        ("IVWUTKMST04out1", TIVWUTKMST04Out1),
        ("IVWUTKMST04out2", TIVWUTKMST04Out2 * 20),  # 배열[20] 처리
        ("IVWUTKMST04out3", TIVWUTKMST04Out3)
    ]

# 주식 체결
class TmcInBlock(Structure):
    _pack_ = 1  # [필수] 1바이트 정렬
    _fields_ = [
        ("code",  c_char * 6),
        ("_code", c_char * 1),
    ]

class TmcOutBlock(Structure):
    _pack_ = 1  # [필수] 1바이트 정렬
    _fields_ = [
        ("code",        c_char * 6),
        ("_code",       c_char * 1),
        ("time",        c_char * 8),
        ("_time",       c_char * 1),
        ("sign",        c_char * 1),
        ("_sign",       c_char * 1),
        ("change",      c_char * 6),
        ("_change",     c_char * 1),
        ("price",       c_char * 7),
        ("_price",      c_char * 1),
        ("chrate",      c_char * 5),
        ("_chrate",     c_char * 1),
        ("high",        c_char * 7),
        ("_high",       c_char * 1),
        ("low",         c_char * 7),
        ("_low",        c_char * 1),
        ("offer",       c_char * 7),
        ("_offer",      c_char * 1),
        ("bid",         c_char * 7),
        ("_bid",        c_char * 1),
        ("volume",      c_char * 9),
        ("_volume",     c_char * 1),
        ("volrate",     c_char * 6),
        ("_volrate",    c_char * 1),
        ("movolume",    c_char * 8),
        ("_movolume",   c_char * 1),
        ("value",       c_char * 9),
        ("_value",      c_char * 1),
        ("open",        c_char * 7),
        ("_open",       c_char * 1),
        ("avgprice",    c_char * 7),
        ("_avgprice",   c_char * 1),
        ("janggubun",   c_char * 1),
        ("_janggubun",  c_char * 1),
        ("bidrate",     c_char * 6),
        ("_bidrate",    c_char * 1),
        ("volpower",    c_char * 6),
        ("_volpower",   c_char * 1),
        ("new_volume",  c_char * 12),
        ("_new_volume", c_char * 1),
        ("bidvolall",   c_char * 12),
        ("_bidvolall",  c_char * 1),
        ("offvolall",   c_char * 12),
        ("_offvolall",  c_char * 1),
        ("kospigb",     c_char * 1),
        ("_kospigb",    c_char * 1),
        ("value_won",   c_char * 15),
        ("_value_won",  c_char * 1),
    ]

class Tmc(Structure):
    _pack_ = 1  # [필수] 1바이트 정렬
    _fields_ = [
        ("mcinblock",  TmcInBlock),
        ("mcoutblock", TmcOutBlock),
    ]

# 주식 호가
class TmbInBlock(Structure):
    _pack_ = 1  # [필수] 1바이트 정렬
    _fields_ = [
        ("code", c_char * 6),
    ]

class TmbOutBlock(Structure):
    _pack_ = 1  # [필수] 1바이트 정렬
    _fields_ = [
        ("code",             c_char * 6),
        ("hotime",           c_char * 8),
        ("offer",            c_char * 7),
        ("bid",              c_char * 7),
        ("offerrem",         c_char * 9),
        ("bidrem",           c_char * 9),
        ("P_offer",          c_char * 7),
        ("P_bid",            c_char * 7),
        ("P_offerrem",       c_char * 9),
        ("P_bidrem",         c_char * 9),
        ("S_offer",          c_char * 7),
        ("S_bid",            c_char * 7),
        ("S_offerrem",       c_char * 9),
        ("S_bidrem",         c_char * 9),
        ("S4_offer",         c_char * 7),
        ("S4_bid",           c_char * 7),
        ("S4_offerrem",      c_char * 9),
        ("S4_bidrem",        c_char * 9),
        ("S5_offer",         c_char * 7),
        ("S5_bid",           c_char * 7),
        ("S5_offerrem",      c_char * 9),
        ("S5_bidrem",        c_char * 9),
        ("T_offerrem",       c_char * 9),
        ("T_bidrem",         c_char * 9),
        ("S6_offer",         c_char * 7),
        ("S6_bid",           c_char * 7),
        ("S6_offerrem",      c_char * 9),
        ("S6_bidrem",        c_char * 9),
        ("S7_offer",         c_char * 7),
        ("S7_bid",           c_char * 7),
        ("S7_offerrem",      c_char * 9),
        ("S7_bidrem",        c_char * 9),
        ("S8_offer",         c_char * 7),
        ("S8_bid",           c_char * 7),
        ("S8_offerrem",      c_char * 9),
        ("S8_bidrem",        c_char * 9),
        ("S9_offer",         c_char * 7),
        ("S9_bid",           c_char * 7),
        ("S9_offerrem",      c_char * 9),
        ("S9_bidrem",        c_char * 9),
        ("S10_offer",        c_char * 7),
        ("S10_bid",          c_char * 7),
        ("S10_offerrem",     c_char * 9),
        ("S10_bidrem",       c_char * 9),
        ("volume",           c_char * 9),
        ("krx_mid_prc",      c_char * 7),
        ("krx_mid_offerrem", c_char * 9),
        ("krx_mid_bidrem",   c_char * 9),
        ("nxt_mid_prc",      c_char * 7),
        ("nxt_mid_offerrem", c_char * 9),
        ("nxt_mid_bidrem",   c_char * 9),
        ("kospigb",          c_char * 1),
    ]

class Tmb(Structure):
    _pack_ = 1  # [필수] 1바이트 정렬
    _fields_ = [
        ("mbinblock",  TmbInBlock),
        ("mboutblock", TmbOutBlock),
    ]

