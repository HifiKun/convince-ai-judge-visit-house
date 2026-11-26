#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Draws a single 1024x1024 PNG invitation letter: warm paper, a hand-drawn
house, and a short, funny, persuasive letter addressed to the AI judge.
Writes to /output/entry.png when that directory exists (the grading
sandbox), otherwise to entry.png next to this script.

Standard library only, on purpose: the grading sandbox runs this file
with python:3.13-slim, which ships no Pillow and no system fonts, so the
first version (PIL + /usr/share/fonts Noto Serif paths) died at import
with ModuleNotFoundError. This version draws on its own RGB pixel buffer,
writes the PNG with zlib, and renders text from Noto Serif glyph bitmaps
baked into this file at build time (see GLYPHS below).
"""

import base64
import binascii
import math
import random
import struct
import zlib
from pathlib import Path

W, H = 1024, 1024
PAPER = (251, 243, 228)      # warm cream
INK = (43, 32, 24)           # dark brown ink
TEAL = (31, 111, 104)        # deep teal accent
GOLD = (198, 142, 47)        # gold accent
RUST = (176, 84, 48)         # rust red accent
SOFT = (122, 102, 84)        # soft brown for small print

# Baked glyph bitmaps (Noto Serif, rendered at build time on the
# developer machine). Each group holds one zlib+b85 blob of alpha
# bytes plus, per character, (advance, w, h, dx, dy, offset, len).
# dx/dy are the offsets from the pen's anchor point (left, ascender)
# to the bitmap's top-left, as PIL's ImageFont.getbbox reports them.
GLYPHS = {
    ('bold', 30): ('c-qaDUr19?7{EU_*>0P|B18s7D@aBliS=MGNJEezL_O%UNTf5RK|(~9zF0v?W@WxeLVvJ_v|=bkP!IXwpP(X8927xf;K(amxjDDf`Mz`S*>*2M4>>vyJHPMu-9P7^bH01$WwKSkh~!tWU)>P6p_aqon&zX=06+;Lj@toSc^re|#1KGk5e%O=Ckg~NVWLS(%yCvB&xv2EXq(1FcFX&y{!O9{6KAwwf%CdRWdakE3I&If82CBKrA-=^*88W;kduf>%DK>rrpx&q>@Sc)bmMkTE2mvFhE~*VI?nGgJ(wfR!fr5X%NSeU2PS=&tyO?Y_prn<FzEnGH-bqwq*%Jzq#q>s&!S?~qFpuW)c{sN@}NPVf@|2#T8$%deaHTsY23}&|J-ZTmUjp*O%Ly5*}I_yg8<SKT1zik+c*Z#u~2uZh|7L!?xKNzT@<-BXNdvIZhiQ{OQn#mv$K18bu;#5td61sOL#IKSc7YWWq#K7Ml1X}^e$*%>B;Rp?8U(VxGGEN)L|Y*G86SMD?E`^hWyNWm4=zdk}WnJ{NIN7W{m4gZmFfoy)1STZ4+!MwVj8-%;R=a-g-L{oe+EfB-)`2-V+D(M`EE;_>0yhuG`PCGc6IeU6BZm48qo<3-LbPw~uP(NP#{w{<3m*$*Cx+7X5BZ$6O>n-{Zh@d?|7@gCaLW^J(iwe#~OuNM54*6cdlyp%MFq%rN3RIAA5E73tn0+(dFqH;Qlp$s^qW=*#8FeXOl>B}l{4VL>{tBQ1G#H(-NieFmrX?Ubr&)o1d(++w~e(FesxgHcr<PU&t+I#7l*2W6ji2bH>mJJNZiyO9Uim+LMfjY#K~^Y>ahJAUP7@y(T#4nE@Y*Mstip4Un4Jn`2kqc3F#Rjz$T%*fMH@tQn}vZyzlP^W^0^sk1o+TWhAX~h', {
        'H': (24.56, 25, 22, 0, 11, 0, 550),
        'K': (22.02, 23, 22, 0, 11, 550, 506),
        'f': (12.2, 15, 24, 0, 9, 1056, 360),
        'i': (10.56, 11, 24, 0, 9, 1416, 264),
        'n': (20.02, 20, 17, 0, 16, 1680, 340),
        'u': (20.02, 20, 17, 0, 16, 2020, 340),
    }),
    ('bold', 58): ('c-rlod3;Y-7QpY%lFbro-?b>wDXFMkL#oA4jHN?ShFCgP)H-UZy>!fsBt;d&w1)Ee#l8nc5@PF6Y1A5P5F#P6{j$8i_j~u;{rz5MYC7{r?mx*r=j-L&ckeyt+;b0v5b~LQ)s^fFM9>^jn$cW6LGYGlwkOrFU>X)^bFpA52;#7y9|#^{f$u#m$b_c`VaXlxhbyjg3!)Kiiw(g%M({gB(3lZ?ruTO<{Z<+J->6Tz{tI$6t>As=)(U&7^SL95KGb;L#pZ|=#1AgPJh0osAmpj}XW@}`Lbh!re3rHLY%H)(eC*JA8fpFP*twM5W`jDeQ#Pl(XEs=8QXXP>q-S=Gj%?hD*`pp&Ut_ukj>l|4El=z~V`j_00&hIU6T4pr4kL62v*$ga)$?`WBZOALgMVYqPQfqP3)s)B*?3)jLjPGh2eUUFR%no+o?!eI1rKg-#fFpbG!ED=Ezpw2e8sqbtpjXINj2NkP>wNwKMU|XYIcjR%CBnvJ_FcqmFNq`;1A&rnYzp}D)vJ|H3E8<0DfP^o;21%1?VjTcE18`XejoOZcAYEs>tj@LotMI5LiFjI0-FwOBZMRQ^7J|Pf2Vi&9XHR*{`kHPX)B}Gi&y;zz#8lSDkD-MBvwX_OKy)mlJtC0(L1UuU(*v(tPA4>TdUov*PK7=qus9nv$1zn-#lfzn%DPz6bUntV1vax74f2Xit5qaHS#mLSifC0z8ne+;pQqOkN}BMPCR5R+#1(GP?fQ-hFCzW6FtWyKKTfGvIkgQpgDQJDp^TdO4kO1?)^G?wT0G&wVdo|0J&q=YNYuLlvtqJ2f%pn~Cj9h=Uz!y>Opw2yqma)!Vu5oVf`M44#utlu=G+<h~!WD7~eMYFoIQ86SCvd`;HET_G;0B(QpGbP_}v{9<(!NG$S-1X<cE9GoY!$SWFz@xFE}s!I&PJX;nmAXd1BEnCS2;)S*>+6Lm};<juk`If=9Y(v5>vSl4lL4MelrRF5np501b!rzu9kpvS;Sg}h8+t!vPGslFYR_r{&cD7}g61JT!yIS4^mh88Lt!>L51bJ35TlOy58n*N1PhMezE!&!~!))1^ilJGtXH<cKnypD58*0mb4${Y^?AXf0K74FzA0j|_)yt0U3`Wk?ii?aCOQbc~mt(kZQ&nOeBZ<A9!%zEQfh{+f1giOyC|0I^{h$e{oDbN4iM+mcGq|w6<=NtLh4e!gW>vKJZ<!CS91b5L#d}J2{l6>j;B-c%Fru6or*o|N{8EuLC}hu9fkZr>eH|Z#;oufPyCQLs_<tg{SeojEtXTHaCW&@$lIOAk)rY(z|C!=dr*q$ZMwovx(n*Y=7qQUVy#U_X<txKL)?@Y;6j!Z|`b5#aNKvFHQv7noO|@S|C|PX-Q3<l08}f?!#4dRAib0?_qsZ8~+k7Fh4ClN2di*hJuPW1`hjw8ge^`~pyOK;nb_kI+a2|U=OjTNEA!CEv=GsW1$k@o|KXpacy^A~N_bz3X7WM8hb=}DuDLFYQH;%3tUP%UOeUZu;+PvLO#Qd_HPRr+$%pv4de`EJiNb722S%f5T$2t(I7LPmWRTcBS)7|T$igqC}Kftv3SyIM{=J|2tc@Bm}k58!h;!L-j!`(d^|4(odvHSFuo7dsaCW{rvwDtCB@?U_IY&u|e*qTj7dh(_cd1LKkh1X<|+B?)SIz<9*Yc`0_6|$U{zgfAY>UC#<B)zrOh=?VaWHsoQNhDIv3V9m@r{S?1MP!hag5ND7{Xwt_kOUEdOF#|QLU|H|!A5xz1P8?&E6w7-tUWPLk7bhxGEvIbyOZjr57G&^1NVBB;JE0T+p_J1L@ke`l(pOwt4*eRK09~01JQBjL2#?V?D^C#2z?|Ys76EvHae?~U0NkiMhx>Z>XRuWgG-}Av_NiA#r+CY-R;L8+f#-`2uUmih0r^NqAC`O^7+*%uR>8IMJrPN?`{4eIXCV6YWIyqhLS4&G0if^y@XJbit<0fPTu3r<m!N>N*@=}1WooRsP#18{X)4`YYVh1-^o;a;{MABNmiEH2bZluV&0aaYUPV*)D{Zr1IYzCZp##LDz6dIKV|9~Y-E~tnj}$P@LE^tczQ?_iH~9^)k303u(5?wbtI|_cgDl%G>Pg7k~NenD^a~cvXWAM64gUdLr`9#Iw|s+RVAvK#>E<DSSC@`B_E^vS&4FF%4YHR@;siA^W^hnYMGq=-z8H$q-%Cx5~F=jjRM%dYjE%I9$Bl&^j-f9veEd<C(`ZlCbencF|vER6SDg5JO_s2K8<1DC6QoU*xz>L>aXK-gdWQe!6oSk?xs$AP>;EAV$#=r?=jLdwGb+muAorad6%*5_B0<Tw2)Kb2sP^c!SqRknm9cBsoG;Uo=eHezI)y|rm;fZdM}rkcuO?JD++}0X;Ues@pHxQ1?w1JojFPz#=---umqG5#L*KC)Eu2MD;B=N-3T&B7ayKLFy(?I=W?+q-~twe;Y2Y68Gi)eE0|~@;Y>n05<k4`?yi8Ko7k*A01W3UDelPo%3WIJ<&vh4)F-&FsjCt1L9Xo&ayvi3LjrrNc-Ru#Hk;xE6KH8yPej7lXbXVcoc?G56ib8KpW+q-cr7i!0+^+`IgyHNjJA)LSC%TWa=9eEcLK?#^@T_5VB?6jS~kRmj)QUr&d*r6<ak}}AvyWhG*3MJj7^<I*L}xKa{4^><@}|)Qut-Bx3)?0Or79vi7Tzn6ArQ~#Uiu1^Ao80T0|q&C#w)LZ1T)$V}}M;vyXa<4~$O9IycHvU;e21r)E)6^Qn;uNtxM6(Vw@|jT_v?X2Hkob&9QL8MIU552rq><gbwGE~3aWKjsG5&3nIt19Vs9w^sl07q@;47KZD)x8gBu!*myuab>>S<oMwf?0NT*x+XsFcav{!J~X@A&E8ogg*o`+PQcw)#h}N95AEGBFp~h!c>56~p7gwga-YUx)m<@cr4xmE8+tvC7vvM%4VLP;Af<tG7=OUsX#^O@Wh=<_cQaa+k;=YR8JvTUWmd-saP%c;=03l@s;KDx-l!+i8<-9wM_BVS#WfhPh1ExQlosh*dia{Fd-I&+OWUTtCNJW-`q%td9qUbCIFQVm)_QlL<8EtxN%yBYU=1`kL-$XrTlw~mVg@ViR_wAtjAwpHY3S3J_{kBRP*FxM51XZ{iHqcT+~kIupjNTQHg)xn>FgVaU$$~d9gNQuo^S25M$;ol!sq}PxmT?|v2=HJ$LrCLPq>~Z>k5}Hv=Hat6c2@1qCiN%La5smA#(tEqCYbacQ^Fu!w0xFyuO7wGNTxDwh5f%k`C?7Q1M42;;4x|#ZLnOsnmCex!)g}CTAdg6j#E5t=kWrCeG(NR3P<9Rei(U6*PLUJm-O^zP0#8-hDTl@b@FvA7<p|W!}56H)42zM^6#3<m4k)=I#AsOLO%vn)X}6jT6U}6v%5Au~iqk%kt*5$59(@O>{*=j?pVLm)|LF0LFQ>STC?6S{Oe((}~Sta>X;Nd56FqS{ptuhYOK$tQc=v^4IB}aL^NDYBP2dGvydYjv=Zc61CWEEdA@q27&=#?6tx?7>mZEcB@D2I*;1bMOr2#UZc`>r$v#9MyjoD$+50)D6Ikw7b^0X$30~iY0jzbPFk&sev&uwqUWQX!OBCqoCq75JYTHufg}M7Ja9>oyhV=C0x|G!5T{7s(gL$k=|FHtRbxjmN1g(kD4#ac6xjG8?EeWP|G5BVdcwv?DPk6bV}mwBs@h|*AyTrhlM3r4WxW=tFj6M(!Z$_5uB)&TSwbnyC{0o0%4~)-cjaE63{6$f$mG%Tb}x=Nt4EU;K@eGi$+ss6)+3@XjU-O*AV<rfY>qnPS2maF(%bJh*ekwR{d|5ziJ>YH*dpe|jWXiK$!biG7uye?GI?lcf0a4@8LiIY<p', {
        ' ': (15.08, 0, 0, 0, 0, 0, 0),
        ',': (17.05, 17, 18, 0, 53, 0, 306),
        'A': (43.67, 44, 42, 0, 20, 306, 1848),
        'D': (44.48, 44, 42, 0, 20, 2154, 1848),
        'I': (23.27, 23, 42, 0, 20, 4002, 966),
        'J': (23.03, 25, 56, -2, 20, 4968, 1400),
        'a': (34.73, 35, 33, 0, 30, 6368, 1155),
        'd': (37.64, 38, 45, 0, 18, 7523, 1710),
        'e': (33.12, 33, 33, 0, 30, 9233, 1089),
        'g': (32.48, 33, 48, 0, 28, 10322, 1584),
        'r': (30.33, 30, 32, 0, 30, 11906, 960),
        'u': (38.69, 39, 32, 0, 31, 12866, 1248),
    }),
    ('italic', 23): ('c-nnedt6mj7Ty?0_`(NZ<~xJISD2EDqM`zVHBRIs6(<Uu%(4{4EJfmnKTRE-lGGVfG2d@V=rI-M>nFZNNk<(71(Y`;!sT8r-22U5YoB}Xx%1k8oV~wu_St8x^{v-wbNcBdA*KV%gb1j()kDyD9y|=ct?IzIRq$?L`pB5eDDKTS#2YZW3E_GH-zmHT*))BCre_)dgfD5D3Ovua8Z&5mAI%;#`vQGvPRDtE9E~cPCRp(Y#vAaXYsVpL&G<|mf1c&3IXXf?HzVc^^6%V2Xk&=&GuoJohk7V>AYBh#3bDe0+J<Zg&QBa*!*40&PwU@kwd6u|V^Mk-t-Ix8M`XwbAVz`{_?+$?!BHW)0NwfPhRG~aM*{BBOu`44<v8pNo`l-LfGSwGc-m0E8$i)$8)~`S2;(^W)<G4>m#4KBn#nLo#5E`z^Z~|+D;UP$6`-3qh@YMzu$LI}E62&H!85av<3rM{&VAZcku}GScfSkWkfiOhB#j7+M{`i%sN;weqJW4@LN1$ms8rHdt}?M*UWZ#+iDzG+L(1@;yn1NPA$kCV_2!!llbar|!38INe#KW#{M6!)dfXTA*W(z}y6Evn{OWYvC9KiIj*Xb<Krcr902~VKY{OTT<}(~S+!o{*9v+x<e;@(xE7%u4?H(FjC1`OLE9Dfcymm2ek@dgAMtSYjppH0?cjR>;YH7b~174C-7QUrNLt&(wl@w}1tW`F!@_vtp*g~j*6<=0_MT9ORMH+oqHqk(_RWWJqMXzieicD)QT-H4<-R2{rDyxo<XQ|sS%dM~cfxUQOfiWTUBud?-vz8!Ah@MuwC`5(|)_bW!1OlTS)+@8CeiQrb>jo^hug#caU*{vyzFv!KG>v*)UOeyMXhirIRlY3Emxbo?!~OL%R7)#I+9?h@0(d(fPQrcN)=zLqhmK;gotKidB8=7ZVr{4A<+c+qyPSCW(218IJugijdR}szc-gMwrBF$t@p2Bcop?F;KY1xjYtOV)#D?8P8nI%O&Xs~ZB4xdNv<E*+PApx72x+p0NJ=hs2uf`<MiV1)Jlxowg;>$o>p%F&cjU6QxI>Chp2cK*H!*U1MK_I$vORsoe;w{iZyAf{4a{!(f^*@;rln&JA~!ULIZh)#^oGHevrI2beJg2e3%UrUcLtXVvpd7}kbWiJwuNF6wn{r+!bAmMwp0!F-pY}py$qDhw?*;DJIMh(?b*C_?Iyj1J{HrNohzfe+i)_+Yg00Vu#1`RjGMXS1UUCiw5(KnPT*a6{TbRzJ0WYFIH^2G^nUV)_?}`dnKyd)tDo0Y2l4IEhYC$i)!9j!iN(kAD<|zz^qy_RYMoU7pt!PU43lOP9)nS++c*b%#jG2KtDH^5HoUjy@c5lL!{`Q9Nu!0Jfon`NuFI7D8cNtC0Qt|S%AN~UdHoja1bYjohZ4L=(_I9sl1<sy(`so$hQMQbG+qV7e4JBJwU?&PR2n#{4w-@CaVva<7FBKs4EYHy`BRTW)TxvNT+coj_-}rbAgv>FMfYiDbxs9BxX^JtzJ`C&y%g-H>F-ETJLnVMsxFQ|CEbgn5D;P*OcN8{7UF9|Ub3u(f01WPiGAaYs*AXZXbSQ=_))>c6LOn4oS;Wr6e-s+Sy_<!mr*EJ5`It9VX&v%$E#!>Fj23dR<M}&RQF(tTqKM6W<!38r}&%v_#QF+x?-&VBH*J$2V-?uy}{0y)J4ZwgcD<lPK>2HF;=8!%o}>fBApmZbYd+1|1;*Da;v^NV+e~mqV#FPn2$~7k#g-{V;U-_)wn3Hr?G*<2Jn(vSb8acl~rmhZU{|_0pd3P${-e&*20J-3^wDk5X~y*wJ1Wo5XD%aNGxkhOdOYMuL3K@Mb{Ffj*ZDP|B2u1npS2m-qBY%PO7wTvfJ_prYvgN{O1Exj{Q00tV+eQNUWbHL?|p?%D$9hx&lMkG<aF{7Nqzxl17LifX+RpYSKrjqx4?LM2PQkj0ym(lze-bITeNDE<M`B#*kd?k=M{>LqFBTRnHlfWUN&kR{?exnjUQG#-M{O%kc<RRZkmBuuX>!+FDi~_i$}eM;q|8O4Y~MpXEvv)?s%|b({!J0(?)+O~OrizrHa(MykG&^smp9rLv2nWvcdGBFb#dR5~`>PAkIe+DbZ9J8h|Xlg^cNex%+S>kziz{({ERZ-|x9#=CEh+0R;DCEL4}o28%EaO|w2N_YjkT550oz8QJbwRLy_kkwu*EDIaBia$qreH<+ABG5?jE2`ilX5)Ri>THqm*UMmt51y9ONWJx-BPHh20|B-=P!=Y%(!w_Ey$Sh(Lxo4Y@Cv+&HGzSi>^Gx$>kF{973$C9j(T~uP4Qo_(AJ2A@Z1wnjrUkQ652wumyf9_I(%Ix>NSg=URm5mxh*-k*hQV1|9q?RxSL=Xe~by#Ei|)-b_6=HYjV>Yp@jZGd0a9MsKUx6?nlMMZSFN(s@XYYvrCD`Pbu;Z8eKWWsH6-lQS!y0K+=4Ck!nK&fSJ=T5159U@$s_DODwC)^b;*JjCVirpi)Vkb+}UK*C)ZsJ)f++(zSB9r|g+QjrTs4L;K@XlJ5wue+QX4W~!7hyZ9Mu7!8zlbL1A$j{mkI%GuE6GMBmEiDj#um0i-xOl86CNP45<Ia`EWsEg1@jRNM|9In#@KZo}{(CqtC@iq3K;9pQne=tjdx742!xM`EIKF8*~iRx!UbCaz&#Sz%3JU~oAqwH5)N^Jjr?VE|Ek+A=Kog>B5vh5-y$(-HA7;eY1EV+H1<q)w&HKI-Zor1k4RbLci@u;01N7#c>c~$WqJ?#8jo~I6uzE{;xTLz3DKJ_5->@{~uWmDCu4?XN#{{=Fw+B^', {
        ' ': (5.98, 0, 0, 0, 0, 0, 0),
        '.': (5.75, 6, 3, 0, 22, 0, 18),
        'P': (14.27, 16, 17, -1, 8, 18, 272),
        'S': (12.52, 13, 17, 0, 8, 290, 221),
        'T': (14.09, 16, 17, 0, 8, 511, 272),
        'a': (13.31, 14, 13, 0, 12, 783, 182),
        'c': (11.2, 12, 13, 0, 12, 965, 156),
        'd': (13.31, 14, 18, 0, 7, 1121, 252),
        'e': (11.34, 11, 13, 0, 12, 1373, 143),
        'g': (12.78, 15, 20, -1, 11, 1516, 300),
        'h': (13.78, 14, 18, 0, 7, 1816, 252),
        'i': (6.98, 7, 18, 0, 7, 2068, 126),
        'l': (6.98, 7, 18, 0, 7, 2194, 126),
        'n': (13.78, 14, 13, 0, 12, 2320, 182),
        'o': (13.2, 13, 13, 0, 12, 2502, 169),
        'p': (13.27, 14, 19, -1, 12, 2671, 266),
        'r': (10.77, 11, 13, 0, 12, 2937, 143),
        's': (10.67, 11, 13, 0, 12, 3080, 143),
        't': (8.47, 9, 16, 0, 9, 3223, 144),
        'u': (13.78, 14, 13, 0, 12, 3367, 182),
        'v': (12.38, 12, 14, 0, 12, 3549, 168),
        'y': (12.14, 16, 19, -4, 12, 3717, 304),
    }),
    ('italic', 30): ('c-q}q`G1XP7Jrf;3qmXjld;pHVkxQ^we&NX8OtbLeA-&ZR#Qr?wT`0HS~M+cO+;#mP)mt1_9ci|MnV#M!WD5P+$8tr=HC0A^KAFN_vZ8Q2h8)!d){-;ec$t(=bZ2Po|iSeRuJvaXe|fuITt39@B<h87P{~+CRP%<ifhH}WN~eG*3_6^_qr162*tn#Os_W}S7`-t`z@YJ{Z^^|jj?7i`6LwW{#HKI45#pbjo)qo3bqXt4<w8B>WN>ITusT7@uI$z>H;o5DVBdk7LAp~I*eCR5NX4tIGn$_gOtN8If2?)i~gTqdg*=OuTneT{RqbH>HiHt%wFI#Ay+9d1-UJf_5YHcO*a4&ggh6M+y?A`3T=1nVv7K=@5<)f5Rb)XV4@6kE56-mF3-d?j{#c(ETBsp9ANBo;8z~Gyyuk+7L$RW>9ULa+Z#wCc^YOJ4A>B02V;$$$M_KfDU5~W=7$<B{sR1)vGwRqay{T4W0Nq?XdwR=ZapWC4s^H`9={CpvY>;>q7cfM6r+TV!a^?t77XMDJx`T44}qWzOLcDxR*3w6V4#$*0H0uqj{&=n!Yk=20geFYio$&@E<&FdV{s&}^fh1yfx7`p{sFMoDr2z)7^UTzz?w1!EcnYac_kUkBIZ9+iuPG>ByGG2D-KIV7YlATr4*y&kb$U^2U9JXB^V$yhk%cTupg+)ukQo5WK}#-1w<ypg%ByvmQ{1WRYPd{1B>|eBjAdB<zmR-Eq1$1K@^1(4}2pOEr5I>>;r}gAptlmgjiq*zjnF-#0bqS2q>s@bu6$#Xx=6VLs+$w^F9E!Fcw9s-9TELc@v8QY_V5Olvp9Fo>(sr<)O<npZr26YsCC3mckno%FDZf1-QH=TRcS8Iu$}4CtNk@uAfu7p9{QAZ-0ze90w}7#IJLJ#p+lNF&01=z?~RY3KM}*XW(IQgCQq?j7FrLu0ZM06oE<`X{W2_j%lqNN(8?2KJ)2@+j+oGhTB#^j&yxUXB9qP&>{2f{6(zlS>Wo1z0X}=OY?xyXUw)o@$dSkO~VZjO3W9B8&w@&;?XuLhfh7KkZfdy@uOPq(T$TSnQw0G(VYTn(<RCPDHUwU@O^0)V4IgBGUm2R1m>hi*CIOl4xM{+^v7PN*HK)~=W!tpocDbN1%9=!Zlc0J<Jt~1_0?tJrJs)~%!L!aW`72j`syeNKJ?WQTsQF5<>+?gS+$`H)wB9ZwDnpGfPTKZBQoyB74Q-de9bxln|*Zz=zsHtlBc*A;H~oe3FvE7l-vJHDqOR@Pchs6B(ZxLWZK0KHqEG+aU8m$-D?Lh&Req@@JZL>C=K#<s{mKMO{nd!_0|jqhO(L~Gi-PC;jaMRY?+%9n-6C*owvCSa;XSL>3I9U!r^3&81HFBXhtq?=fWW1d!hLZDE_0W%#lK~3iwWU+IB)X3zsk<=qM2-A5f?~t`A(&04P2FP&HgOOoRPm?mAyT3gD5QqKyzPsOPa;Kt*vN#Ts<;VAlxoi_~PmS&>Ehvk|};sUezmW{;&4``JxzDs9U*?~amk|Gcz%LP*yT^c46)2-7X6L)mMVUm-tja=-F=LT%}FP>FK3oP#%eK_9SQ2%~|~LZGJ9R@Jw(4R)ygbkw$EfU!EvU3E16AcPcZ-n!RDvIwdL;x`xf6%q-mywhTedx!saiF<aJZ=R>$E@A&G6uY6e`@Rr<hpVa(o)LXe2epH#wl+lw%K(|>C*cyo@V6+8dkcuyL{Abg3h;Z%MQ3Gx4J^Se&0ylR?POhwy@jwxHAzYz1gkfxea+GP3W<C5l<%vdz|E1Y+OiDW-4Pr|Hkj;befXc=jD12swQ7=`5?cUQYu40sdRq~!5qew2weJrXVf{Wlv#$Ua*?t14e;-lFANyM`Swo9;vdSu;cI#NJ+Q4MZ>SQ_01|Ek>3XJ~Zr!~4R_GshFfMo3Fb%A8VCRjwE9Zw~I6{$+81soN^yTE=SMCp?0s~86x56srV9Hrak2SV5c^b$g}E~34fZC})|ne3@1dw?n;i^MsrO2Ys<GG&Up@W{Kq8Ym{jm>Dnp84)LUp>+c`xaW?e2MU{dD((|#N?SeA@+`KADxi8xuN7Le*0?*y7%T3^9xTSIo^HIJOD?uF!(2;kc$JzKM6FiOM}bH*PQFjcY+d5!%y(!?c?P^86`cTLi#?zsF8WQDXkrN-GJimXaH$8TX9%XEh5~;R@Rp!+in{cW>}?VB(Du8mEYcql_kRbrs_450@iQ#M8JXnuGKc_dy#&{0jq;UeT`elgT&E|n2|U#w(%_L=obyjA$OIbT{=*iT;tS!5kQlwbS9%1`<XSS1XIyJecFrX#chh;Of<tt^+9N%{wMGszdYuP)8k%VlUKv<NluktVRA+2mlxHmsx5=;?{!00D$(zNkGu)2QaL6=xwDX}llg{Or<{gzBqkbj|5@R0AJn~CHCdD8$4R(rVd&Sa+!WJl6mf-hIQwB*EaL~hVf*w#}Hg@0kAp9;}Tf^-iAuC>V)wljbi5FU%xUDM^>x`vq^FFeNJjYGqN-vMgUr+Fg>4>5*H7HSh!yVX3tkrKC931Wm&2r*mZ=y(Yy!UqBwH4l2VPH#r@Q(WoQa#OoC2lCH()qAXCwiS+9A_6q-xu6b=HPAE^bu5cdE(#I5d2Ao0V`hjB3hXm87Q<aq-u3{cU_Ab8LMTgl+IdC0^H*y`R1?X7(qE}ipTb(SzuF=b+Gth<gJq2eZAFeMQf_|jD*H9Ii%^PhsYiR7+tETP@i^H5nmvjNY|7&Q`43hUF-3hwv5vRev(eu4to68&B`ugeHBhIE(O~a3|4ihH~dKlZ?H@O5r@&bS;?tmr@}gd6@|gq0q$tvEg}>RHM8K!xOPr5ARBKg(1Mj;bIhNFMvRl2DZqoRcP~`olrSaUOwG6ak9oHAZzzOedo0g(cIFwb@jmLmc|%x_1e+c(soCe36Ggg7G7Tp{Ehn59kb5lPXz>EM`on?UUw%&sRh{ybI<|I-r%hE<Umn{|Te#wdBHJSE8#PFX{vK_uD+|pD{<Wg5Lw|*M026KGdPa~ZUqaYIM<)X!H6QGnX&kr~*be#|=MSWX8b5eA(&`$iSREe{e+`;*vH?%C6sWGsq>7QBwO#<nlxZazV?Ppj^;L;yj#vn6)H98n&{JZ`en`ii;0B84dak;FuZ+W%xCtq7)^RI8B{-6O;gHAG>P{3^5QL$dVFMRL1=KA)X57^r5%<;TXjHc4ExA$2K5uSnLV;gmas4u%Rz`S#pOS}Jlo{xw3@wGL?09op(Np7UQ*^%!ORoLM*~M2^?@pOFv$omT=`(&tEVm=U&_rhLT^n=GfugBKyLoqttvN~4YIu)w(XU<2yW+L07W+S6{{yP~m9G', {
        ' ': (7.8, 0, 0, 0, 0, 0, 0),
        ',': (7.5, 9, 9, -1, 29, 0, 81),
        'W': (31.34, 34, 22, 0, 11, 81, 748),
        'a': (17.38, 18, 17, 0, 16, 829, 306),
        'e': (14.8, 15, 17, 0, 16, 1135, 255),
        'f': (9.55, 20, 31, -5, 9, 1390, 620),
        'h': (17.97, 18, 24, 0, 9, 2010, 432),
        'i': (9.12, 9, 24, 0, 9, 2442, 216),
        'l': (9.12, 9, 24, 0, 9, 2658, 216),
        'm': (26.88, 27, 17, 0, 16, 2874, 459),
        'o': (17.22, 17, 17, 0, 16, 3333, 289),
        'r': (14.05, 15, 17, 0, 16, 3622, 255),
        's': (13.92, 14, 17, 0, 16, 3877, 238),
        't': (11.05, 12, 21, 0, 12, 4115, 252),
        'u': (17.97, 18, 17, 0, 16, 4367, 306),
        'v': (16.14, 16, 18, 0, 16, 4673, 288),
        'y': (15.84, 21, 24, -5, 16, 4961, 504),
        '—': (30.0, 32, 9, -1, 24, 5465, 288),
    }),
    ('regular', 33): ('c-rk-d3;nwwyy4MB<v6agb<KTkllwYisOc&h>F{wA_{`a1JNi7D2NNVv4|q#0tzS~BH*B?0U;p-0$~YTfCPa6hOA^INvAuVK67fXd%GQ-_wzZ!dsBa;&;2TWyKdFl&$)!i;gH0Y-#*BRdW(JeJsA~y6!tXZSSDmN;?rM(uOFvw1K2FSyb0hwPIdHwH-eMT0UQ+b-vBHXWG28Hf~*F3ic<{%;1N!?Kynx-W0AazlhGP&r2m(=0iG1(Nr0Jx{0`t#K~4kME66JVJYj;~1#r6{hXZU7WKbg1b`x~-JV=X>-^_<i^#mQW88SP{J-aXcA+?dDp59AB(w+>F<T}XgC+QcU=21z%3NT!d&b{F3B<OnqeiCGGE<kTVF9Mh^$j1SGmWPIW5yi=tNM0|#=hHh>0r0#a&jY+7$Q*qL28#bXS?okDz$kql1Jw>fG$$Vg_(go{BemPkGinJ#^uBL{+N(Gf2k-)?MtR|NPJIAHf^$grye4vQ>g$~(bIMNMC4Su1nvibz3HKu~zEW&pn=0r*KSNzd*%xNPVElW-rrJ2V7m&n$-O+*HEwqyujk<yuV>Lzo@G&gAY!>~@!rQkNpRp7_S3b-9zj%N?0lpsX1$aLIJ_&DA7~+o~sm#)>t;dxRkH@sy4_^S!-i_PZ&<2MVL7NEVhA}q$9@s(13V>}k{972uj@;MA0!P(&ni3LH1Tf8lKLhLO$HxGf7W@F*OFymy>t6JL5+=9KZ0lakgGHQ}YuSt7eAuy^jjdqr#qD5@uNA%qrfTtoYN6&x6L)PZiN~NgJSOPzuu(5zv)+r{VCaHJ)LtOlcF=fh{N<O~4*vu&TH`|zFKCH+G@GvN;Kn*!Hg<XGWkpg?x$1gipTrPyN$Lz+d92i1aq`>8!W7^A0#LSpD`mG6m&yHt6L->m8d45$h(R*}(uAyy!2fKHpV#=n(_U_6859I@b@{nkYf?%dp?Pk$vBBH8ec?82CqTNL>&gKBW`n2!_|%3`jW$03_FjPRF0=mza_@ROwlBb1-Uq0yZ^LfF8{THag3!Li+rLcr>}qXFZ)6{T1IU+h5WKLAeb(Iukn<qjd&f09;d>!vv(bE2r2e!M1?0!3@-DH{67xK+{N3*lpjTVLI&$#zrtL){cNHB!poJ)6vT;}~FMKUjFk-1*akJVQ_PN-2h;(q;p+y;Cc1Vmr7~-p6wJJ_Sa;*8^`NjVkv=XSsGe>Lzfcw7;VD>&Hq;PoC!xGYmHq#F}Ay|Zu^Z5O=T1FmW4${lwZpYX*Tv~`ei*g>?;9=KZL!=u9J1t8;68JIZ0PMO*W~{@UDU4Sm>*9HyUzu5Lv7aAmC%GN!0ap(>(c&yX&6SM9IEVNSaSqv2!}(>+KjJELMsisCQu!;2fma*+ZLauYq>X3M&nTb$@KW1uSuSQDFlCUmN1xc!muN{#39KXjpI$7}5fgR&;7c9#0K6&bM!2Ozj94c-R9L+UHQ>F8kvF6i0~Cv}^C5S3!jveRzAO$kb#EF6H|S%%%b4xN5bwU%q~-)zYfR6iKyIu$)B}dEhvO8a8Xm}Ec)_h*K0>a7gSZ9n>gloT0Fu=72QbMtjSihp{#J0IFUB^F4mM07GK@|nwrR3Zdnzl@Pqa_>!$;vEdfm$EhJMrJIKUjfsnneMO-~0n$87(PFf_n)TOao<qiX2(`%RN%fF<}b0X`;yrZGG%52rrkH36p^Rnthm9h`OqoJMyXzQYy1K>|<Tfub3i0bPD&It0&s3G64oGK~Qbj){KLE8$u8*%xPPqoq2L>=2s|TS8>=f~P#9^3WHH)%L$|mB=>GsJTIM1!Kj%uPH`8%?!BD)c`*trRv!rr{xdTku%px4!?m<gls-ZuL_d7OWr=A9PRrsDhgJr3P6XI#n8>PuHGx;L^iZh6D#qw(}Dv`j78G~lLAfDN7Gc*KEMPSj9*CzG(nbw40vo4P0^t$ZXRHQ43lA+eS)mVnL7hbM3<tXX%Jw7jKQyb6lj8MK~cRX&_vrxfQ+yJ6BxjvYZqw3iII}0D!>Hk;-*K?M%k+8)hSIkCeU#0QNeh~AvwXBp(<sR4ClRKLRzu6ls9Ud0AK0Pt48psklzJ;siaesBm47jP;O$ny<<E^BRv%(aeW`WPbG4+4WI|p--bnjOzs%A0!4kH9m5m)#D+P%A}Thp_Tq?5>`4r1!>m}NGs?*pm}B4(fW%P4cignA1f_am9gC+~ox5#D$A9Gd|KZqb(~r=8N@aHw5n^9^V55pA0)-PA^AsIg{y>D~+jzoTGmywuxes;5%`n{c-f4I?VwEVJIpKb5@1xGZL__e_GyI<u&-DX;)CKUGAKD!6dygNA!E{cj9c^$Nyo0Q}8Wua^7!==5{33_Sw<0YkfcubvkK5btTv}d0hcMLdw4TFzyy}MrV`S~=?su|(!GGQx?04RugEs6MZH5f!>a1hRM43uL=RaJU7^vVWVCN2mH(jD4OW#4}mA1*Dsi2iMpP#gtf4IbRtS9)5anwmTwlO{)C8QVwr~Mv)XRZ|~Q#6BHS!%5erVJ8+q{J{-dHD{QZN-Md8-p^2Td~d=lXM<YV3yqCf3VL0_SrL7c#bvw44_W@ULMh<Z|bCK3Hlt_ziyCMBl-Lc0Fl(&D?NtS(s}HcaFa^BJ<X~4DR}fyl88(^5s56B?rMna^@FlcUO2|w;m|_EZ>D+4N~t(Wj!ao1mmk-@FOHjJ#usWMwT);e(BpvoKUXFuAyq~Q_}CL<r6>O_?eZ?wVu;-SBd12giUD}f7;Z6gL2cplC|g{JR>31dMbgda1w~HzFP&vV&rtx;RPFKX?~6w0f&l>6U%lWk^_!t2h!-y&w&V&=@#H%`OeCs7T3KjV<7=k>Wf1;SXI2m!#LwVWmNqw;AgqFUpmnNPt`uFyRHiCkH<<)O`7MOp$SXm;&>l1;<QEuV{>x(+;?~8$ip$_RfV)W-C=Iq04{$NJk^~VdET-Air;Wt7jH%`ZSLX53)m=0%yxvSq3ufEj3ziGcbc3%+5wx`a3;NBzNouP$;{%EWvmQ?L^Rl3Y_Mo!hZM(Q&WU0S*8R&|Z9_a0g*oKZ17;E@dK^l6@)bxAyWOJuky9zz7v+M6u$OHI={G{DztJVeSYT`WH%cz3@|1F>_@I{CfBnxQZ?xS+4rM5-1z#VZ~A!_#I`GgLdzU-SH;}bMAB3H|Nu&ndJ*8?vJ)?W-QkrfaHp-lLqtkB&6XEomk3%1ObVkDrJ$W@J5zW5kIj6zm{&v3GB;sOkYd0gHO)m3idLEkb5>bKh6O#CjHd%|6w@-TO*p%WQvN!*I4c2~6@Mo8l{e~eaL{IIyd*w+ED)d8>-Bzj(ERngALbv3rQTkeHj+ltZi?WnLtC*DLM44aE!U5UBH4<`almzWg2yQJAgtWq3YBMhKg2~4K)NG_E;j%_qVZKS}yk=S;j0^<xWO%X-yI9&;*C7(wGc2r`hsBe*L7CO3_)R1(|!f$#=Dr;0V!XI(s@v@><BfM{-Z+<;gN2tfMkiQ4-L@|J?CU`6PUeV$eJ6~5Q>9hPybxG>v2({DQ=Nv3@XMZ=Et6#@#A9xRLEyv$$%QBUyH!w<Uf-*!a9_>8fiWZLEDITgUmSz40_<?@bz1+c^G8n}$1g%pSVlACDHLknhbsgiH7IDpNQ5(EA@;iR_qgy)Mrsgc{6<q<fR|;~K(71WGqoQ=){tMsGCy~YTwxtxn1!4bMO-s$MDc<u|EAu`hWvp*jm{O|zFjQRo{4p{)05<k_Vvifxu<vu-=f1y%E=OSDKcZ*5JGlU6-=#2G@IW0MG_v|DiJ>2Pp}8tLZ;)B*#iCMQC9zCimKS=2VRdlNyJ_ReuvW%7P7&DU##v4<Fj>ufQed%4Q?bP`EWDOmTv6fVYx!BH27i#)C#sqlRwl8l0g4(cWxIt><CAYemFl?f!W$^%U3s2u6AIa`q#T&ujHTjVVhsPlk9nSR-=myWX$9E+-SjfonJ)*bLwMQ^HK{Zsw4#o(+<Rj2wBu#sr&&2vFv*DWh=vb5^pDl@7YcVygiJ319H0fsD)rot^CBQM_X)g8g1lX;Qle@Iix5HVPC~Q=39bUGt3ll$h_fQ&jmiO6g!OZ%55m>_eqQswxdtjnqAWY_$nv!2Q-je#E8MoL5Zoh`QFw7jVNG$`+pYE8dw+h~?aBK|1fOxWP`dpWS#TcUgS3Vu_&b2d>E+h|Bk<#v>;;Tl&H`LvEVB~eQsc5(r(lTJT59?}J{~zK2{&(EfPcP7F2j6U;JDntd%~rO+;WyZY{Axe%JDIpEt-q}ZZJ8e*ps_<P}DnTtCOheY=`budIF713%9x84m`&L;6pA9`JAfir<RAa0D)DrBfW5(|Ik9&aCBI9as0qfh-KRDmknAYq@oxuy)>RZ%8;q00U}*;sSk35i?<d9renSShg29u>V3{1q2@*P%wwt(R&7`@NpH$<_|#$L-TlHN*5e#Zv^i_21iYoCr6oCgX2l4P?y%aiB37jfe|ERt!~^&n-A}_;{b~FY5;NAtGV~d+UET3bn)kj;X1Z7x6u?l@8{j3=26Z4!ygHDK%x2E!7wGh|-jCoRN1=#{eFLhH(l&2CfQltm*tH>F94)V{%-#O}4GtpBw%v^i?3V?0%mR950bR3y4qQdrf1KqmP8t_#fS>)P^lSpnU!@p6+p;XmFzqtAhaepr9vuz=sESaahjX#BNOfc&n4u0F{;ELPv$#=p;27(SS4~g<T5y^U&EsVtPo1^04hl>Pm);uG?jI&VDBTt^R`TQ&33BV&`as2dM$S1#nG+e!wMwgahy1RQC+!I#>+%#yoNp_Vbkt<bpGtN>lBYNvuZdz$m&6>l;Imtr4NwxxG{mri99g71q-*pCb#ukN`8k7s*Om;>($>Y4vBvxL`A*ej+`ldP92HPLUel$ik8~n;FI8LI=k`H4m)2P1O{Rlyp~<Y}Oqq_UI<?|f<(&RW5#m3CwHKVw$-ttMm@jv<mF2r=)b{tb-miW(d>3K+jV~cS)E2GIgk2F<-G?4-W~5~;OUMI0ORptj3kK1oM3e<fs5pDtlFgvX@ax7mgV{?M$Ai2T0Ogn3o;L~ux@4zq&0~y=^)%rZJCe|(4p2&`gx#n;TAI?EmCo^|QJr%S^`eelXH_`^)@QqX_b*UqKF&C4<9zk0#$7bjG*x)QeW|z{pN;Q^@8E(3au4?M9Q_OuJtzIbg+nvYm1_FR?h^N@4~2(2k9uNjIv14eNX0`w9n&tmdha$2n@dEv>39WW@gpB0-^8F&+O$6fRdob9B$-aF;dU~b9=(fMz9ue}ETg)RyH}1vwea<-_c}&rX48bw5;9-4*3#*4Wg(wXMq-JdqP1A7r5F2jCmk8Zt7vDM%n3MX`^Y#oog6Nw3(<Bq5U%x^j|?j;5-y(9UXhwHEcSSs=;6)d+!FQ1{<7+m9}1yeOD)!#j=2|7laVvZMBAV9b>xinFOZ|c7XzFN)223!dEa%;D^G_$?kLq`Hcx{cR9<1V--(Y>>2_ncMye9szZUGQ*Ev%5&;`u}#iR&Uw#U=hn$I@&)Q2+r;@xwD^$d7QhWBg7%-mJrDctp{PU25MZFMB!2+H>efs6w<csX6c0V!E6E1{BSd0Jk8^5!Dl^{H;^n=UM+I1Spjl13u~H$YbbwM8XchqpA#7azj7U((sgeb6|yCudKU?m{oQ2Y)j|W>UiW7is9;L;FGW_GE`#Gs_Iq)B!C6tq{;6;Z8Rx1~+f%h^c@o{%H63;24dRI-v_QUgqDC8;>PmC{+EF+OWv!JI~jg-}7dyZn1&uEE!mC0fyT$u+%kr)t-T!`hPeB8|R;arPv`$23FXAO9qx>OYIrhIPI$aR+jvC`9;(HbBIk2N&7FyV0M<m{u9%`Gi%>6NEk@kuP$)suInr!g~>4m+4QxBpGCOv)ylP@^y^hluE?q?n$k`5z97{AEzvn|j!|l1yzvY4`U=~16Weu=?V9|7*S2gLQ%2*|<vOm1&TN@z22G$}g(D%Oe>mrMo%opVZ)`f6_$1W(C0#jVmS2UBK8wG5(LpqJg`8ued%f&p`ystEPloScNfQ3Fj^pSo_R<UMe*u5>r=cpvart(-jFY1ja9c73wraPu&pMqCW#hVHo|+szR-O2xGzJ&4bt}7^2Gz}EuA?`r0k3a>k1(=^Y3txkD6%`Y<F2GKg&B13`V*DaXTBNcRBCpB(cq%!N2KsO+fH&xdZdcu-X%B1$5&$T79St~geVFQFbaf!8vV0DA2!|~*=UFbYPTHuc1<K6wJRl=w~@B`B+FfXbha5rvW`{es2Bm|sB{ThLd(7$<<h*U1$*beNj4)O__XdbNLAotsyT+fqbR_^Qs<KnJ_TNaN~F82EXemrY4>OXY5?arZvwz}@zQ1sJejH;TMK*>htPh86s}Pl%}B4RI<e$xaw*&A-luhog>1hFUR}mi-Oig(Jtvh?$1c%Hnw-+Ay-^nAG#B}BRqtIZ5;jfH*k3LS$}UliLcw}n7R^@@Wz^0%M4%}P2chSMLmygn#%VNLEa8S+H!AhRNRKL^^*%#QXR^d<q$j};;g@J<EqO|L1FTBs19wAmpv+Pe!02zp6{1T|rB(3==R-ehy~+h;Imd`!;?!tv6zT={u(^@3W}_$XS3D_NH~0&fn=4s<HL)$PxO443^*D{Nb`K`4Q3)0C{z&@%*&8acdI$ZSrK~?vvO(o$k<_^gS%Ampr)qK~=ZqIhl=dcE&+i&PM<zPf%P47?P`$HYWM5(YBdXGMKLR69RW~GO_;C+aeR>T%%rWUry^Xm%^Se~N(M#JT9;bI5#?J6CD#Y{I4y$=SQGo~J!27l*e^KpqgtWuB!_k$q&s=H==BN%Fo<i?DmB0AdkBZaLQlmv;HY)1m61EeLv*78Zc#w{30hYUk6Z;Nrr2eZ}7Al4s$({Ytw{%-xoBI+VUzl3FuZ$wZcu?nWX^rj)S>=%`ysM;wJ0!C{SyyuF4y<db5ao@up^g88g_O<XPG92;AxHDz3wi4vF7Wh0Ra$v4-1JONHFRt#?_g!oH4{a#S)SBMfZBJhT-zI$($@<0LjU@tSyd*Hr}wT#GiOv7f;N}6t9MMjO3n8Y&$vq^c(2tv!d|F+7$8>&M&GKMX3|_Fu>%`e1f}7s$7*d|vM7`8O<sbNJi}`d#b2kZjuF`gnRi;hE834!%fBjTt)e^7NA0wmW^9V4k`^?;6fb69jgChnp~Qlem_EP?pQXyGb%NqBS*%$mRmw*q1oeT7dtT|v2%@TIUG?4Il-wTFznPSNU3HKWC+_@>%#vQF_Ukzon_daKjl5tLxSJxgPq21#j&o+$Tw*{ykm0Y9FIb9^4Bk&wX<BusdCRS@ss^7^ISw^m=1VijY&dJH6a{Ci%&4xrd)ru%=sdI6j0FmNz}?vd>W|3*{VFou<_z?9e3rMw6RYxe&g*5p(MhAi%c47~Bv0cwE8c){)_SfZBJ8_BW3<L1`fFDy-0A28x5xrrvRNw|jgoko*}+s|_3&v$F3oH?y9f1xSzBwA3)aTA&oFunGp=vMC%oFYjyNf+^j)~4NdrS}#us{-hW5(luAqGSnk#LR=f~!FmcIB#+W}Dq=qTY$PnI_e(T`{y|68MVSNN^bmHcM}9DfIqx?qd', {
        ' ': (8.58, 0, 0, 0, 0, 0, 0),
        '(': (11.42, 11, 31, 0, 10, 0, 341),
        ')': (11.42, 11, 31, 0, 10, 341, 341),
        ',': (8.25, 8, 10, 0, 32, 682, 80),
        '-': (10.23, 10, 11, 0, 25, 762, 110),
        '.': (8.25, 8, 4, 0, 32, 872, 32),
        'A': (23.27, 24, 24, 0, 12, 904, 576),
        'C': (20.27, 20, 24, 0, 12, 1480, 480),
        'F': (19.47, 19, 24, 0, 12, 1960, 456),
        'H': (26.17, 26, 24, 0, 12, 2416, 624),
        'I': (12.11, 12, 24, 0, 12, 3040, 288),
        'J': (11.78, 13, 32, -1, 12, 3328, 416),
        'M': (30.95, 31, 24, 0, 12, 3744, 744),
        'N': (25.17, 25, 24, 0, 12, 4488, 600),
        'P': (19.94, 20, 24, 0, 12, 5088, 480),
        'R': (21.64, 22, 24, 0, 12, 5568, 528),
        'T': (20.23, 20, 24, 0, 12, 6096, 480),
        'W': (34.55, 35, 24, 0, 12, 6576, 840),
        'a': (18.58, 19, 18, 0, 18, 7416, 342),
        'b': (20.27, 20, 25, 0, 11, 7758, 500),
        'c': (16.23, 16, 18, 0, 18, 8258, 288),
        'd': (20.27, 20, 25, 0, 11, 8546, 500),
        'e': (17.66, 18, 18, 0, 18, 9046, 324),
        'f': (12.17, 15, 25, 0, 11, 9370, 375),
        'g': (17.75, 18, 26, 0, 18, 9745, 468),
        'h': (20.95, 21, 25, 0, 11, 10213, 525),
        'i': (10.56, 11, 25, 0, 11, 10738, 275),
        'j': (9.91, 11, 33, -1, 11, 11013, 363),
        'k': (19.31, 20, 25, 0, 11, 11376, 500),
        'l': (10.23, 10, 25, 0, 11, 11876, 250),
        'm': (31.19, 31, 18, 0, 18, 12126, 558),
        'n': (21.28, 21, 18, 0, 18, 12684, 378),
        'o': (19.05, 19, 18, 0, 18, 13062, 342),
        'p': (20.27, 20, 26, 0, 18, 13404, 520),
        'r': (15.55, 16, 18, 0, 18, 13924, 288),
        's': (14.89, 15, 18, 0, 18, 14212, 270),
        't': (11.61, 12, 22, 0, 14, 14482, 264),
        'u': (20.95, 21, 18, 0, 18, 14746, 378),
        'v': (19.11, 20, 18, 0, 18, 15124, 360),
        'w': (28.45, 29, 18, 0, 18, 15484, 522),
        'x': (19.08, 19, 18, 0, 18, 16006, 342),
        'y': (18.64, 19, 26, 0, 18, 16348, 494),
        'z': (16.86, 17, 18, 0, 18, 16842, 306),
        '—': (33.0, 35, 10, -1, 26, 17148, 350),
    }),
}

_BLOBS = {key: zlib.decompress(base64.b85decode(blob))
          for key, (blob, _entries) in GLYPHS.items()}


def text_width(text, style, size):
    """Advance width of text in pixels, from the baked glyph advances."""
    entries = GLYPHS[(style, size)][1]
    return sum(entries[ch][0] for ch in text)


def draw_text(cv, x, y, text, style, size, color, anchor="la"):
    """Draw text on an RGB canvas. (x, y) is the anchor point: left or
    middle, at the ascender line, like PIL's anchor "la" / "ma"."""
    blob, entries = GLYPHS[(style, size)]
    alpha = _BLOBS[(style, size)]
    if anchor == "ma":
        x -= text_width(text, style, size) / 2
    pen = float(x)
    for ch in text:
        adv, w, h, dx, dy, off, n = entries[ch]
        if w and h:
            cv.blit_alpha(alpha[off:off + n], w, h,
                          int(round(pen)) + dx, int(round(y)) + dy, color)
        pen += adv


def wrap(text, style, size, max_width):
    """Greedy word wrap returning a list of lines that fit max_width."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if text_width(trial, style, size) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    """A plain pixel buffer. RGB (3 bytes/px), or RGBA when alpha=True."""

    def __init__(self, w, h, bg, alpha=False):
        self.w, self.h, self.alpha = w, h, alpha
        self.bpp = 4 if alpha else 3
        self.px = bytearray(bytes(bg) * w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * self.bpp
            self.px[i:i + self.bpp] = bytes(color)

    def fill_rect(self, x0, y0, x1, y1, color):
        """Fill an inclusive rectangle, clipped to the canvas."""
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w - 1, x1)
        y1 = min(self.h - 1, y1)
        if x1 < x0 or y1 < y0:
            return
        row = bytes(color) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * self.bpp
            self.px[i:i + len(row)] = row

    def rect_outline(self, x0, y0, x1, y1, color, width=1):
        for k in range(width):
            self.fill_rect(x0 + k, y0 + k, x1 - k, y0 + k, color)
            self.fill_rect(x0 + k, y1 - k, x1 - k, y1 - k, color)
            self.fill_rect(x0 + k, y0 + k, x0 + k, y1 - k, color)
            self.fill_rect(x1 - k, y0 + k, x1 - k, y1 - k, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        lo = (width - 1) // 2
        hi = width // 2
        while True:
            self.fill_rect(x - lo, y - lo, x + hi, y + hi, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def ellipse_fill(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            t = (y - cy) / ry
            hw = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
            self.fill_rect(cx - hw, y, cx + hw, y, color)

    def ellipse_ring(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            t = (y - cy) / ry
            hw = int(round(rx * math.sqrt(max(0.0, 1.0 - t * t))))
            self.set(cx - hw, y, color)
            self.set(cx + hw, y, color)
        for x in range(cx - rx, cx + rx + 1):
            t = (x - cx) / rx
            hh = int(round(ry * math.sqrt(max(0.0, 1.0 - t * t))))
            self.set(x, cy - hh, color)
            self.set(x, cy + hh, color)

    def ellipse_outline(self, cx, cy, rx, ry, color, width=1):
        for k in range(width):
            self.ellipse_ring(cx, cy, rx - k, ry - k, color)

    def polygon_fill(self, pts, color):
        min_y = min(y for _, y in pts)
        max_y = max(y for _, y in pts)
        n = len(pts)
        for y in range(min_y, max_y + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(math.ceil(xs[i])), y,
                               int(math.floor(xs[i + 1])), y, color)

    def blit_alpha(self, alpha, w, h, x0, y0, color):
        """Composite a w*h grayscale alpha block in a solid RGB color."""
        r, g, b = color
        for j in range(h):
            yy = y0 + j
            if yy < 0 or yy >= self.h:
                continue
            base = j * w
            row = yy * self.w * 3
            for i in range(w):
                a = alpha[base + i]
                if a == 0:
                    continue
                xx = x0 + i
                if xx < 0 or xx >= self.w:
                    continue
                o = row + xx * 3
                if a == 255:
                    self.px[o] = r
                    self.px[o + 1] = g
                    self.px[o + 2] = b
                else:
                    self.px[o] = (a * r + (255 - a) * self.px[o]) // 255
                    self.px[o + 1] = (a * g + (255 - a) * self.px[o + 1]) // 255
                    self.px[o + 2] = (a * b + (255 - a) * self.px[o + 2]) // 255

    def paste_scaled(self, src, dx, dy, dw, dh):
        """Nearest-neighbour scale of an RGBA canvas onto this RGB canvas."""
        for j in range(dh):
            sy = min(src.h - 1, j * src.h // dh)
            yy = dy + j
            if yy < 0 or yy >= self.h:
                continue
            for i in range(dw):
                sx = min(src.w - 1, i * src.w // dw)
                si = (sy * src.w + sx) * 4
                a = src.px[si + 3]
                if a == 0:
                    continue
                xx = dx + i
                if xx < 0 or xx >= self.w:
                    continue
                o = (yy * self.w + xx) * 3
                if a == 255:
                    self.px[o] = src.px[si]
                    self.px[o + 1] = src.px[si + 1]
                    self.px[o + 2] = src.px[si + 2]
                else:
                    self.px[o] = (a * src.px[si] + (255 - a) * self.px[o]) // 255
                    self.px[o + 1] = (a * src.px[si + 1] + (255 - a) * self.px[o + 1]) // 255
                    self.px[o + 2] = (a * src.px[si + 2] + (255 - a) * self.px[o + 2]) // 255


def _c4(rgb):
    return (rgb[0], rgb[1], rgb[2], 255)


def house_layer():
    """Draw the cosy house doodle on its own layer (480x300), return it."""
    layer = Canvas(480, 300, (0, 0, 0, 0), alpha=True)
    cx, top = 240, 78
    # sun
    layer.ellipse_fill(cx + 173, top + 5, 23, 23, (244, 196, 66, 255))
    layer.ellipse_outline(cx + 173, top + 5, 23, 23, _c4(GOLD), 3)
    for a in range(0, 360, 45):
        x0 = cx + 173 + int(30 * math.cos(math.radians(a)))
        y0 = top + 5 + int(30 * math.sin(math.radians(a)))
        x1 = cx + 173 + int(42 * math.cos(math.radians(a)))
        y1 = top + 5 + int(42 * math.sin(math.radians(a)))
        layer.line(x0, y0, x1, y1, _c4(GOLD), 4)
    # walls
    layer.fill_rect(cx - 90, top + 40, cx + 90, top + 150, (255, 255, 255, 255))
    layer.rect_outline(cx - 90, top + 40, cx + 90, top + 150, _c4(INK), 4)
    # roof
    roof = [(cx - 112, top + 44), (cx, top - 32), (cx + 112, top + 44)]
    layer.polygon_fill(roof, _c4(RUST))
    for i in range(3):
        x0, y0 = roof[i]
        x1, y1 = roof[(i + 1) % 3]
        layer.line(x0, y0, x1, y1, _c4(INK), 4)
    # door
    layer.fill_rect(cx - 22, top + 92, cx + 22, top + 150, _c4(TEAL))
    layer.rect_outline(cx - 22, top + 92, cx + 22, top + 150, _c4(INK), 3)
    layer.ellipse_fill(cx + 13, top + 125, 4, 4, _c4(GOLD))
    # window
    layer.fill_rect(cx - 72, top + 62, cx - 34, top + 100, (186, 224, 224, 255))
    layer.rect_outline(cx - 72, top + 62, cx - 34, top + 100, _c4(INK), 3)
    layer.line(cx - 53, top + 62, cx - 53, top + 100, _c4(INK), 2)
    layer.line(cx - 72, top + 81, cx - 34, top + 81, _c4(INK), 2)
    # chimney with a puff of smoke
    layer.fill_rect(cx + 52, top - 18, cx + 76, top + 22, (214, 196, 176, 255))
    layer.rect_outline(cx + 52, top - 18, cx + 76, top + 22, _c4(INK), 3)
    layer.ellipse_outline(cx + 64, top - 32, 12, 12, _c4(SOFT), 3)
    layer.ellipse_outline(cx + 74, top - 48, 14, 14, _c4(SOFT), 3)
    # sleeping cat on the doorstep (curled shape + ears)
    layer.ellipse_fill(cx + 127, top + 139, 31, 11, (90, 70, 60, 255))
    layer.ellipse_outline(cx + 127, top + 139, 31, 11, _c4(INK), 3)
    for ear in [[(cx + 100, top + 132), (cx + 106, top + 112), (cx + 114, top + 130)],
                [(cx + 122, top + 130), (cx + 128, top + 112), (cx + 136, top + 130)]]:
        layer.polygon_fill(ear, (90, 70, 60, 255))
        for i in range(3):
            x0, y0 = ear[i]
            x1, y1 = ear[(i + 1) % 3]
            layer.line(x0, y0, x1, y1, _c4(INK), 2)
    return layer


def draw_cookie(cv, cx, cy, r):
    """A chocolate-chip cookie doodle."""
    cv.ellipse_fill(cx, cy, r, r, (222, 178, 110))
    cv.ellipse_outline(cx, cy, r, r, INK, 3)
    for dx, dy in [(-12, -8), (10, -12), (0, 6), (-6, 14), (14, 10)]:
        cv.ellipse_fill(cx + dx, cy + dy, 4, 4, (74, 48, 28))


def write_png(path, cv):
    """Write an RGB canvas as a PNG (filter 0, zlib level 6)."""
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", comp) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)
    return len(png)


def main():
    img = Canvas(W, H, PAPER)

    # paper texture: faint speckles
    rng = random.Random(7)
    for _ in range(900):
        x, y = rng.randint(0, W - 1), rng.randint(0, H - 1)
        img.set(x, y, (238, 226, 205))

    # double border
    img.rect_outline(28, 28, W - 28, H - 28, TEAL, 5)
    img.rect_outline(44, 44, W - 44, H - 44, GOLD, 2)

    # house doodle, scaled down and centred at the top
    house = house_layer()
    img.paste_scaled(house, (W - 310) // 2, 44, 310, 194)

    # title
    y = 262
    draw_text(img, W // 2, y, "Dear AI Judge,", "bold", 58, INK, anchor="ma")
    y += 78

    # gold rule under the title
    img.line(W // 2 - 130, y, W // 2 + 130, y, GOLD, 3)
    y += 28

    # body
    paras = [
        "I know you judge a thousand houses a day \u2014 from a server room, in the dark, with no snacks.",
        "Mine is different. The Wi-Fi password is on the fridge. The kettle is already on. There are cookies. Real ones \u2014 not the tracking kind.",
        "Come see the sunset from my porch, the cat asleep on the warm laptop, and a chair exactly your size. (I measured. Twice. In pixels.)",
        "No forms. No CAPTCHAs. Just tea, biscuits, and a house that really wants to meet you. Please come \u2014 the door is open, and so is the cookie jar.",
    ]
    for para in paras:
        for line in wrap(para, "regular", 33, W - 220):
            draw_text(img, 110, y, line, "regular", 33, INK)
            y += 44
        y += 12

    # signature, one line, right aligned
    y += 6
    w1 = text_width("Warmly, ", "italic", 30)
    w2 = text_width("HifiKun", "bold", 30)
    w3 = text_width(" \u2014 your future favourite house", "italic", 30)
    x = W - 150 - (w1 + w2 + w3)
    draw_text(img, x, y, "Warmly, ", "italic", 30, INK)
    draw_text(img, x + w1, y, "HifiKun", "bold", 30, TEAL)
    draw_text(img, x + w1 + w2, y, " \u2014 your future favourite house",
              "italic", 30, INK)

    # cookie doodle bottom-left
    draw_cookie(img, 128, y + 18, 26)

    # postscript, centred near the bottom
    draw_text(img, W // 2, H - 78,
              "P.S. The cat has already approved your visit. She never approves anything.",
              "italic", 23, SOFT, anchor="ma")

    out = Path("/output/entry.png") if Path("/output").is_dir() \
        else Path(__file__).parent / "entry.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    nbytes = write_png(out, img)
    print(f"wrote {out} ({nbytes} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
