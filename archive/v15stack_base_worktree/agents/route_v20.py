# Based on "V20-Adaptive-R1 | Multi-Route Agent" by Kaggle user boatlee,
# published on the Kaggriculture competition Code tab under the Apache
# License 2.0 (licence verified on the notebook page, 2026-08-23):
#   https://www.kaggle.com/code/boatlee/v20-adaptive-r1-multi-route-agent
#
# CHANGES MADE BY WASHAMBA BOTS: none. This is the notebook's own agent,
# decoded from its base85+zlib payload and verified byte-for-byte against the
# SHA-256 the notebook itself publishes
# (8ac34abce129cf5c9456776c90edf7d2233b3a280bbdcf7622628825ef3669a0). It is
# submitted unmodified, deliberately, to establish where this route lands for
# us before we change anything on top of it.
#
# WHY WE SWITCHED ROUTES. We ran a v16-RC5-derived route to a ladder plateau
# at 1,687 (rank 1,223 of 5,940) and spent a day tuning its parameters, which
# was worth +1,306. Measured head to head, contested market, both seats:
#
#     v20            vs our tuned v16 route    24 matches   +8,855   18/24
#     v20            vs the stock v16 route    16 matches   +9,288   13/16
#     HarvestForge-X vs our tuned v16 route    16 matches  +10,997   16/16
#     HarvestForge-X vs v20                    16 matches   -7,972    0/16
#
# v20 beats the other published route on every single match, and beats our own
# agent by seven times what a season of parameter tuning bought. The route
# generation, not the parameters on it, was the constraint the whole time.
# See docs/ROUTE_GENERATIONS.md.

"""BL-MDgogo-10C4S-R0: public-replay consensus route with generic execution guards.

This is a behavioral reconstruction from twelve public traces, not either
team's hidden source policy. Clone preemption is disabled in this experiment.
"""
import base64
import copy
import json
import math
import zlib


_ACTIONS_10C4S_3Q = json.loads(zlib.decompress(base64.b85decode('c-rk<U2j`ia{MoP)`Lk=UwPBm+}K#n$dK(2n}IMGAR7b-HV>1$1^eIQSR#3OPjz)wpF`SS_{juC-+R7KcXf63um5}Y@4x@?x4-^z_D{c_{q*VG{hQz3-+lP_>2ZDbbbj_9zyH_2{rBg;eE#^i-~af}zy8nX&%d6%efQ<B+J~P${pGj2U*7$EcYk(%_WEIScD`)B{_u9aen0uchxPi+=dU+!*LNS!&aY=*|Gd6`_~q<;vHSV^$A>qcUVq&GkE^Grzn@P#_Ws@LKYx0^f74>pw_ndT>kl8lwDp&V$B%EneA<0A`*1iAAJ+Hx`?p@q-@1L=<W-;{)7S1l&8Gr2VD`Fj_FxZpE%`Dhi-W$t{EEEm{r%nRbu^x+KimHR-ZpDDdF#u6nT}`EjxXQ+vR@1beSMj!;AiOwukYsX-!G55kL$<zBAS19xO(8yUCtNLhlfw|Mbs|NKmGsCIQVAPJ2sW=;2aL{Y?Su>dwut^G`Bx`-kFoGTXVS|uJ)zdQJDTJoi4Ed(By!f(5ztcmY1;yV>TI%X2#mz=ri^*?sVu5o;%-p`yp(nDOi^a;cx?+Av{|7*>cbYZDi4*lTY5ZrTSRP-{kWMhVbQt0dthin?8uUckDiVK6^i)58lA-$GzvlFTbRdKKA)^!iRKV`+p~I8v5My!&i9h>{hu5tjXjsH7<}bPo1Bw&h|Zd3+DC+`DtTDjA_B^hx_~W>yN+vY5n-|-Tk|NJv<Wz4PN;r#u6#N<4AL`y|pLp3HQ*>5t;osxXLe|3=8m^UjN4Y&ilBkd$+0m*J+ag^R6);Cq_6}xD`JG7$a~`;9k8fZOcsNeVFz(>ti~Az_B+BQs%0_PuT<6SfEeo1DQu4+K(OnXx!wY0~HUdWcw-`i2COF{1Z>7&-GP+r}S~qTQ-~rVBGH?*&2iS=5K)$Vq50zvmTe4ssuMXv0?q=Y2%+J-}}IZT44Zt(Pb1MAXzju*u~a&#W6G|xSdn$pl}UlhCnA&CtVCf3<QKThL=Y1Ze-y4{<!WN74S0W(bQM~Z;9qVy%97UqGX<s;o(+W{%8tN131kB013`TM`XwW4Oi*VlYfq-{o^2KKOXzzu_h)JTQ7F39t6{asC;5+T~^M_iZ5=0BSn|b07Lqshnd|~F;F~6$!R|ciT8S;>`o8H=I!0%zeFAD1&k)$(OrEp1dWDj*O%fDO~;~#AJ7g?8$jGK0lH8SKIprSJ-^j-W`I4i8<got<yZy)M-G<VevNJiWgo7T2YvrUbg4|=H@B~>=<t?cL2oYbhDvz2eQ?Wh`e7jacx*4ibLrSfmtXe$0gdlQ2Yo^#>cv$0@bU3(^V9nA@h^ZKD8-G~B^EXuynXT11BK)<ro)yD2`+8)BiT2i^!QmiZiZnvhp+k}B_oQ#f=-)b8BJ4rV+v7um=O<Vb*+!xhutNeKTd;Tw|DGh8)7c%z{q2lzcC+y;wp&xZGHXR%&LutK0P<I67g*BEy6z&sMF5lDmdTK*l|DNOkXQ%b!FQ$C$dyx^q}2oFR%K%5g#8=x`YX|EB-NczcYNLa<4D|VsZ;^9v<$$q^Uq7>gA6wGxYg@d?Q2x_rAClt}D}r&f%ms+%iT^7{nHt4{CG)$VTjTa^xYeL1)0w0a-tzZ~4(NFp~IExojm=s4IY~J05*Zqc-lF0#_24+I%X*kLyBM5i}8?nEOu^unvKK6aEpf7`wNEF#_$JqZ4g@HdOWk8*B8*92s!_w8-u}_FUsp0oP(?r5?)|x~k-$+CejjxWKU4DmSiRj;L*M9fwks*-ZQ8(olAGz3~nMl;P<{#%jFEc4j~bC^aX8uQPLv!vyLH0=)A)?f1N#5iO_dl3c`$o-)gM^(;k{2Ta#HPwSO21p$8DMWbMQT4O?m9j&{3AIG!UQ>Jy=zPCL##JT7TwOi&kZXLVlbz?ESZi9vxw=&p-?GZrkebA!W--;Qo%qB=blpI9R->_4~4wE^qbkjHL$aGH+J!Gm=j$MG>X0{u%F?X*?0ZWhW*ABt%Y@MepoDYgYf^P1`5#(@p?cHF#%a1Lla{#mA*stsf9#>x}rbWhnM?d-Q7JCtv)XbE}*WNhrXO>4%NQR)s&hC#rl)D-$ZntTtIBsOvZ+|O<Q8OVS(P*T6P;4J;--;<irRcZ^9fG5Ae;mJD%s;=o|MSbri`=31mwC=y59<B0rJvuoSmrx*$*=%>D#7BiVFB*M=rc$tw_wGAtu4sGSbn7$C=!x2k15~;j^;fbb828UFh|SU^jxsoSng(WdSv8G&+{a0R|pU`V|kGyqAlNIBKw7nR^(%~t;7drA5;$J9XJ_mcLC9|_5sDnXv<dxE{lka#C}Z9ef4nU)~aR>oa67+5DYM8U>*w}s`=W~lRQQ1*Z~;xyNh6i(jYhxXd{5TEIU(<KC$gd95hK9P_sL=En&=>g+5d<k~i=ESyn^?^d|yfR3M{lHG1wX!)g5g(aZ2R0G;k6&+aIpL<2YDgT9--if(@LJ53Dg82&r3RWkRTP;b4ErtZz>LAu8D(VY4o_r7ryV9pOVNM%P?{$Xz(BXjfHHM~dS+m$q~C*|zVLq^#OFDhVR0q1BP#=~g<mWGE3Yi&jFiPWv1-lvECFVhQo%ub26(asu{CR580-D>G@sN}VRgNnT?fjtE;d<>U>@}8LFRttN8%}~j6mR#=EhX$4^*^-064Jk?LPVi~L-$WG=owOZ6(k!V+@_&J;2f7&lsxxs}SqrUMsst=sgSAfk<J<h$Ew-0{$X)1l4s!hrAxsGwrhSpcv|SZ7yc0AFm~ca0dCJi`S*yO$!5U5m7$amenlDgmm7MS=LkVS<I;ZJ;y>LC@&s4(ob+t4ZjwprgsflNb;sh(}`l(NuSm};D=tm)pf|b!H7g=>BEA&smc9odpFhYu+(XA~2=^Kep9aHf`52hHrA+J&s@Uq;_Vv1MmPlExPzC?`n_GX8vk7iAQVR@xY*%T1IbqOg@EJ<^TX*ijz!~m(+N$lXo**w!Gg8!Vhx266R17)}wP(mye&&peS(*{B=pY&URah&<OZNCANR%-uM2#GEhhH1f8G2=;qdEvQ%a<>e8&J43Rsx1d47e}qHgNG)aqdao4k#IPKTfU9p(k^5Z7niMET;}VM;li_lxJo8>!wwNZkCtcjN;pI`G#T6`<}BjHL6&PerHf8~3HWrVjj6R1)vr`nY_50;lEK(~Y%~KZ?1AJ^olBS`$rix-rezM2BZbw(3{ByDvGw)KLk^1oD{5p1d~!gtz6uT!lDz#ajWQ@<ds$AZ;Ly#tl3)>46t;Zxqf<5ZxdHugav}R#B5)WICBX9(KpciT$cf@j@dwLgmU$T6DI?x<4|G3fp<=yow6fsr@H$vTX(tL1?3P`^n`P}<Pnb`*p>Lil08$G10XLY0ZaFu-i=ly-%Sslv#v_QxV~JV7jA_7El9CAMif>FIbMfeiLSrN&>4+n*j$#-bjJ&yMxC1|a)wD@mY|(g%p4=(O2<iROM*A?8%$s)=N!Y%sE-T`e@dd54j#0FT3SxNlpBKBdiR%<lfD-_4alcFVThbLOUY0F1(0Yo2D1|kuNkSAL1TR(=Q~Mi7x{j<8@mS<Ca_FxEmx@w1m229?U(@@9el=|6&_EwxQi*VEP34ddErsiIeTd-aLvE?znidimBuGm412`R07$ZTL-Ivq$+$5OI@j)4Y&bYbW>$)P*?p{LqF%FYP##T%oM3M+oBg&9KNE?}~sSEj;PyJfWPOgaVv4E9PQDw=ntBPhC<C-vW0s{$@)r)VRDg-Ht#xT<S{3}5T-bgXfsa)LO7$jH?>}WZeNFi!ji>`$uMCXgSy5b}*D~uN^C@AGIR^|-(V`*()HBSh;*0pJ*LCcJEr6|@^y+;;vWnMb-wOnr4@~PsAX`x|33TVVIQg;KC`%C;@r`8a2mQsICLS_{YPsj)t$}Uk5M*L26>4KH0AxgCEb<Z<g<^C38Ep)tmjqZ1p_Lir4)RGknGYN&w1AKzPM~DX@wa@jVpVOMJr$h+qS+5Y$>U(jvPey@gU28~Y)^eCbgrMMd@7=)NpNheC*|w_Su2N1!CY%OfxK5HknBUzd&Yab%h(U?F&<W18s|1ZI|4t&KJ)b^{ke+&DFxfTvl$;KedJk^?fF;kEz7z@ir3HXgkqg>vkE!1NErUahw4H*+BwVA6D`97o^r$mxYW)0@G}VPUbyk%}@f)J2K=aV3#}NOla}v2wDRXfoE^mcKjj#qfCMi{+vnZIdm&B_jOi=1CWUw{Xr_UE6T@mMA(S{vzpD_QP#Uf+66~YH*|IJ4Lv@ma8tQIedsCy#<>6^8xZsLlgR1`WpTLXwzezRKFxL4kUW(;JB93#^jln)bjt5Q-~Yh*1dejE7im#y!<_<FuO&sIP?b)a9qUz$j*EkqT%>X!mPs|_Q<l+`TO-0NExGY85cR%M2|RVFsY5%bs!%pEI_k5a8nFA<U=HFEIzrlx*KovSU$`XJ%))$`E4e3O|NlPb)eer&e-5bHZWEOc>qiA~RPku*-hKy4Kg_RZ$4PfJ7O)E9<abiJwCe#Kh@gAQ*2g|o{#tk!=~Ge|<G$E*Q?7Z~>FqzXKFIvuf~jY6(NP&F1xRww|)BIVTcTEm@8UTjDIE{uS`G3VpPfZ`5>iXJ-NMH_8us7@z?XXm&%Ad1IZ(159Ns|Ry|F9M<c?;>L9xIrfkSfX8#xJ`r7wT}?XluDZAX1huvCLglF7A{Mp)Qi9?27#wKPaEE6m3;b6igCMg4vYOgi(?q$Ke5&|&Tm@z56Qs1GSVq~`QX!e$3{RN6{>iYl1~B_B@3Wo_MPbBrKZfa!?DayD9QJ!lxY_+`kN<%Crtxw)FDi*TVJv4RjJ}VY=xGIE|J3v?e_EqJxfsQW!~rm1+^Far9#&B;<BM%C|-b?zN5zCW-A^x$I7oQEE^IBP6(1(B5NXIAj%~Qo}Z#Cnf(!;`Q*qM+;WZOog6-t7f_d{T$G$|Ev+Mw5AGlgqn=zy1+8phMq=8e;)Y}T(Ov=K)|9X+#_Okn)oORNI6tGq63B&|{lgS#m;FK$a^WN;)rM!h)EDAqJ^kUi#O3~977(X&`0WECj>J(r)>YGSc|&>hQ|Uj@#M^H*7GI;ykBQ3HorE#*_{@*i1LnsG((A<xx>%upd_HZ(VBANU-&SmDkeFj<EFZZ4Y3Rksbk?HuddM5y*z}q$1mIa@yPBJ#6seaY@v2-Ssz4@3g%qMOc){VqkxY%_2+x_)giL9m8}<~$l9m6gEFe}7k~mdKi48|ONr3^VA|!EtDgl1UjJ0DT1<hOy6@wNBWkGjRQMF`pMeK~i!qrf)7A4m-6^7{;Fh;f{(ytNZ(?tf_!6#uY$cDzz^%3JlWJ+D&Emv$TOe3XS4bgHtCign>_f}uexdX)JuSzih<XM?xKrW&YlmZ%u)5W(t$q^Or5Z+q)mpmv};Bd+gWA=B!!N#b6e;)RDiMz~B1qZMk$X6qGaklmCQ^9vl&F9D=$vOs?<lKT)u)vZxOhfG=qh9jHvV~U%-4!?cuzkAs#FIz|&zQ!Jr_o8ZK2T3c+~Km2FcNnOH4(USlf8U!u|x&>50u_LCaOtb0#ytkV6HHbV@O=nIHTEdCQ?Jx$P{{9Pd&lwhC{M2s4z4SBY?vwd7#~jlmDD|@VaZxlBlj!Y9%{>$IRMQHRdj<3L?d9#bLFkN(xzP<PI%WBV2`aZ;d!W>hWssCon7%vkJcOYo{*pRqD`Xoo$|$@myFvf{oJIwR)_OVa)ru>YXNu4??;Zu`TkZUs+==CDK@3=%J={>?0y408|WGxrX)|K%a<j0kLn#gT0okxOOSouisD(&hp!l=qI&lM9nn;(;Jd-V}Ub90GF0}EN0!vY6|E2fA3eDKZUmcMy*pYSV_T3#VMrT%gS=JU!A1@G93o$Z>0cjQuB0Ri2(E|La$0YSrUYtp2)YQQUc7&z$0r+f_U3nIW!`xM6A0xl$x(pCBRu(iFKS$#PqY}+m&h;@Hz@odJwIWuEJW^Mh=a*AP$u4nwAMW!d^yd#dJG83-uV8K?GARq-Q~};Jmxq0^iv<WksF8m}qq@Y(xbPg?g2y=s`!nR`qG5s0Ypcq4_4zwyb4jDBw@)nro$D8R|V)fxpKoZ%=-j0@G3bV0Z@|o(%0ulT2~qnaVptV~RpS&kWY@sRmN*)6kkF-@;a6buVcBO5Rrl3qOm$(T7&f{Pq>ewAx76!5da`MUAhR_OriYzKv=b$R^^%Xq9PoF&qrbC~GoO0Nqa+u?R2#B|F^kfDOl4ruCGFFH2)tS*oUW_F2~9Fu<IjU$@4>tQ5<X=L#9=#u7yn`3ms?3~PY_Y=Ynjt2CZ~ZmxGBY)-O@Sq*woo>GG#%}##dYb=+-EV9$IP}r4I&or<p?`u4H%NkQaVn?dn4{l${oxJK>hm`cCnt)EOp4bbr;Aq_xbvw~#$RL@{wM8dW%9z*OLtkY{Ii#hGx9GTzz#ls7)l;k|!EvLIGu4_VzH=j-vpg4z=+e-ty0lnrVY>nshUS21iHdnyq(1P_O5-bLK9Y%H_uLSwa*{c`wz)&cn~DxNULj;l3r|?5<A7UoJh7FQP{kxNk}Wb*JElNInz%-dLZ?EtWCkc5)p?d$6)CM2PTKAA(z_VM54(63L2*k~tmb>KOfy&&2OE8Qxti4A8^96E@PQO-GJHZqo0-91ltwY6oNISA-CQ-@t5%z~({R;vPSp4uOJI#3dJSfRTS{W&cDlyL(t==iAzDXAyt_sVQe`GQnaGvXI43nx7{CqV;82p*k+oG(hhbO|Lo}m&CXJoy1Dcn{MJ4$p>JFtYwC>?tRgiNh7mzkDQFirPPrxCX01I0|6XzH~M|II&)gU6K7Aq|oye&&m_p;v;qo_NFfOs-lAv|&MRA4r9O^9eaP}C9~V}*1mVBM<+AZ1bnhika6Rp;u`g1j=Vb5RMHk!XtfLvu;hJWDOfNJXEb`@j&GIyH(!urD?XTlULyEN$gXX&ja)${Ww!{8?jlU@$$rp|*3w0=h}rqMiAoI+!CVqPYw-MF65F-|v;!7g0!!(I7*PZp&m1p{{~a(Z|o?O3l+cVUUIL1DjIHg;DKR2wSa=r|orsF_8=q5f>U)7feZ_loh><x)(k5!B9qgw~m)n+^nM{wxWv!7mJ^^s=#M@>Zq1$#?*0J-(;Q02Fr>tg(&30NK}OPjtXlgdb{$vD`cOs6rgC|0?DN{FR~0q2Lcz0t0Jq|u%t%CQazUm3VMm)3W;q|;;_M^BB|Rf*V1MY^Nv9IGMwBSBWrTwiIQc7oQW1!Wi~H`*(6z&Ty%}mOZ54!94yvsTBY#hLY!dRI=V(f9Mx7b?7}F6#wS<Jwa%c7Q;~)l5WytT@P=fkGple{oJK=re3}S}MWhawp+Z1P;y-;Neu*sAb*X5SPy!^c7+>eBMtiYOW6UI5Nwo@w2ryndo6Rfntb7PpI_Xlh>W1#c5UTSe(9XU3Z)tyTjQ(CY)ejXlvTcg3yfN*~cj@WoYvWEMA&U54f$BR#U95%i{&8xiji-qn$VcQvu`t8(<UFxdA>Dz^PD>f9)MWd%d0|J8tN$7tv9vZhx`C*EolF9gND-6;rYZy{EN>e~sHNQME1%L)sN~X^4B`RAu?kXEq`8>{vb8dzLNQs(<68|PkI}EvA$4g>m!l|S0Xl-IgbC-+!ERT5tg(dUlFCm>h2s5i2IG#oiZOlxK3_5Ys-HQQskc*oDV=Czq<mHd-NcIbq;*z>k-=G@n#>s`nT7RVlsa^!#Pyq+t^$WfXCicS){;a25enZOSIJ0WHtk$`(pVN9kZ!P^DOJg80L$Tmg4FJ9f4&_kV8pd`;QJVA8lQ<WD>W@Ux<W&BzR!o><3q1{zCP1R$CE3qUF1~suTV<3*u|Hjl=*l-oD3YVZ7yreOPl6~29(4&`;zIfRl&;3v8=aCh4r@hp4e@mmls{_?`OSnD%p`MSSG|Jm+y9@vXw`pydAHO<=0}ojV)uT39T!hFDERefT3Qo-Bw1qE&0I`WacmwnX0dmfRs~p#0qfDvX#p|a5@AZoiPrJ=q$rE8Dt;mRKWv#u(1l3r7Ao*yN(sT6xnqu38Y7bDB?XV0Z}KPXF>oC=UJ!XI)yF9(0PnqtYi{W2h;vE4qli~^~yko63V1)x){|{x{Glx1jvZ+>{8`QG;2YQ;+U>p13G1q&`jqN%qmU%4iDZw#BW(r#LuX$G3=i_Vy4<&BoL-6vh7hqHxgyOLfQdA<cD4}I=zl&WQ!F`8MHU9gDaVLx2*8))H)+nRhD{Zy@gq8Y)LLf-y&b}`kvr=w)UB|YRiCbPR>hsT?FP-t7)BJME0m)YBcf{sloIHU#{Nm%lbl4dabJ5h=nG=Q@X8;19<Z2#Yk^~b@$D}ohPq5>I;x;1c(h!_4QX!nbUEO-tr4KPhJWzt2bIznoBgSOro7qr&O#Bprl9{;9G?PN$QYht0j%-bJ4EOYNN8{Dv4!Fqen2A*0(iP?pZ+>8aFnaQl$N^-IN-;(pq@Tw@9h84A>L%3-q)=#(flYl8&(KsQM#SCs!pM(sgE*<IF(T3e7GbIjOEDr(ALM^w9H7t-*_O${2`cio6B2>Wf;qrm<Jhww<<ImlWkwk(GgPrPM81HMG@IY+k&!#>MrbhQPoOAwQuhQC#PO5+56MsfFw|Rb<qgCl$ruMrdbgDuQYSpb!tSKsiAaomEdrb510>8CBKtb?lAyGm79^DHgj0+j6d9nTfpgPKI3FRfEWH#JKCYe%XMCRu1zz5F+?)s#3O;wiDH<^kvT!5V@^YdO|*!fT%E|skiLprciTIE%jDldmV-{jz#zq^X59`&!aY}?5%`G((B)~q%4Miuw+5CcmdpesS=At!1C4sIAK(E^$IwD)knPojRb##C!?GutajysL{j?5R#{UG1Tz+NjV4oZD7t7>c}cD`^^6?JBG0irZ)9=GOD)kwQsmG}rBh3)bDks_F}an(s-jw;I(s*jWf^7>si`c*Z6#`tRb#d7GG$uVLER@IJIR)8vCh#})Zlp{(1LBJ2%I?Wk5J~}#LVy2BYS?-Wu0V0(g~UDK1s)tHf>##XVtZ3DSXrJRjsZFq2qMdseYc|g*?HX_#8W~*kAyB2O$p6&Y%n{EX~baryybUEfMdZj2BC%>@9VA9%qRSC)QCeV7$XwDyBlwo_6dyBEKxXop0r2E=psh#J<?yc;wqyB(IL5ZpidAeO(_rUa}go`v*gi(_Ob+Qqj8n&QefcZW^=c9r+<FU2~ec0KZJ?Ff8)NDhhE0x<UIP&F=&RHdZi2k2SLoRY5nI!d76H6gguhvRogTu0~(b`D2;Vx?12M2a$o63YcRa#?%G3W1)YBWiEP-nY7|haSAkYn;IId!6_(DR?z#ifP78xB~2K-H8?V9j#!#brsTP>eq4u@lk`K(V7{o@x0!7?P)%Pgb)X^rc8q^j%A{dj$q9Xdh~EhVQ432{t#S3FM+CEVtd^$$-C;_e=0Nl070SnhK1JHl3zN0Zpl2l=QiVLF^TyGE$^`aI$F$XOo1hnZ(cJQ)hts50c2MrCUd5*iC%3Cx#LZ4^^k$Zla-GnLR2YJ!BPW_8oL)+acHLQRdV1r^61L}aK*^g_F(cl;gW*Me6^m2F;UqFLC8}qOr5|SR4d3Qq{R2TazSJWfO1ciZvm2E&td`t(8Ns{Y0$C!s?czJc)(+O$1zwV;QGAm!Zgj#QY><LTr2=R)(<Q}EpsOl+M+~X7lzS}YHzHu`mS$yg_GaD4zOoK{Q$z;~L!_{LTY}V-7&N^CbwjH8wdtL1V3uc0v3nv9xhxD^K~D~JV8ujF+vQBQ44Iq$gs+4UEZRpRL)fUtw<tlU)UcyjFVmLKXa?S#ET1X~gL!!X8JqKjzw>>xbc&a1DMm8?PmDI3wxL!Vh9-ka2bTwAT^p7Y%z`JlVKS(#fTh(?!j1=m3j_(I!gTXWELIb>VgtJ3owG-CBjY+H`UTf%qANzlWfGls1rv8maVo$P5sCEkxH-%=;w(`?Buda^U}Aib7Md@Rt-zWfoXMs-BRo^$li%7EWcg&m5*{##xE~>3u$FQ*PM?hFZsf(V)M_c4>h0?k1Z~NDo0?9Nx6F=;D8+JFOKi_)pv;gu0_`LmHG{ODv9;{WB#rEAQK-L$bjZ9Wu%?+oN)ZJCRJt%!OuJRRima(2RRvTaPFE*mj&Lo1lvm~xm0~yvM%z%D%tDG3X81=EdN%6QZQ>Hjd9_}#WSgE5m##H-JZ%WsG9RRNbx~KFYIn7a4W1TIOi0&N#xs?tN~K|y9xf_dLB$cPLAigf7v!WH&{KKi^<J!?0rLwi{GFP>+^Kgf;0kV{#ulj+*<mG4jO4ATrC`1_BRff)j5m$dJa!#zjJ+ZjP#rUVi9niE0650t{WfCm5+)iW!p5xl8Z68<tMk@5$$N*pdC>vUsHG>g|6%^O-Z&q7SI>w3DIMFMF>^_M?rT~qZ|Wwa`X?>zqED45VPf*z54l}+x(7uyglN2y+L9ErOmC~O+@A9CWUMJ+G|`#QUd^tQB>t4KTXRJoYPV#Hh@8fr8l1UNBFbgzx)15l!(&}cIZf(<>hA^@TtIA9>X8a$E^<e)J9cny@sN|(R*n?%I6ksQXE)AG2(%poW5xp{lsA!ARvg&&O;VM$-kuU|N>aF{tEV6wl}MHPbxA=_>EWjo={ap*bxK};U*lGi*S>jtcz^iTmv1H?cwfQKp1)%0;s%Fa&`)Z2UE7J>hux27-=y(D(6+;nVPgbu4d|!8Km8w;Fh$h')).decode('utf-8'))
_ACTIONS_8C6S_3Q = json.loads(zlib.decompress(base64.b85decode('c-rk<U2j`ia{MoP)`Lk=UwPBm+}K#n$dK(2n}IMGAR7b-HV>1$1^eIQSR#3OPjz)wpF`SS_{juC-+R7KcXf63um5}Y@4x@?x4-^z_D{c_{q*VG{hQz3-+lP_>2ZDbbbj_9zyH_2{rBg;eE#^i-~af}zy8nX&%d6%efQ<B+J~P${pGj2U*7$EcYk(%_WEIScD`)B{_u9aen0uchxPi+=dU+!*LNS!&aY=*|Gd6`_~q<;vHSV^$A>qcUVq&GkE^Grzn@P#_Ws@LKYx0^f74>pw_ndT>kl8lwDp&V$B%EneA<0A`*1iAAJ+Hx`?p@q-@1L=<W-;{)7S1l&8Gr2VD`Fj_FxZpE%`Dhi-W$t{EEEm{r%nRbu^x+KimHR-ZpDDdF#u6nT}`EjxXQ+vR@1beSMj!;AiOwukYsX-!G55kL$<zBAS19xO(8yUCtNLhlfw|Mbs|NKmGsCIQVAPJ2sW=;2aL{Y?Su>dwut^G`Bx`-kFoGTXVS|uJ)zdQJDTJoi4Ed(By!f(5ztcmY1;yV>TI%X2#mz=ri^*?sVu5o;%-p`yp(nDOi^a;cx?+Av{|7*>cbYZDi4*lTY5ZrTSRP-{kWMhVbQt0dthin?8uUckDiVK6^i)58lA-$GzvlFTbRdKKA)^!iRKV`+p~I8v5My!&i9h>{hu5tjXjsH7<}bPo1Bw&h|Zd3+DC+`DtTDjA_B^hx_~W>yN+vY5n-|-Tk|NJv<Wz4PN;r#u6#N<4AL`y|pLp3HQ*>5t;osxXLe|3=8m^UjN4Y&ilBkd$+0m*J+ag^R6);Cq_6}xD`JG7$a~`;9k8fZOcsNeVFz(>ti~Az_B+BQs%0_PuT<6SfEeo1DQu4+K(OnXx!wY0~HUdWcw-`i2COF{1Z>7&-GP+r}S~qTQ-~rVBGH?*&2iS=5K)$Vq50zvmTe4ssuMXv0?q=Y2%+J-}}IZT44Zt(Pb1MAXzju*u~a&#W6G|xSdn$pl}UlhCnA&CtVCf3<QKThL=Y1Ze-y4{<!WN74S0W(bQM~Z;9qVy%97UqGX<s;o(+W{%8tN131kB013`TM`XwW4Oi*VlYfq-{o^2KKOXzzu_h)JTQ7F39t6{asC;5+T~^M_iZ5=0BSn|b07Lqshnd|~F;F~6$!R|ciT8S;>`o8H=I!0%zeFAD1&k)$(OrEp1dWDj*O%fDO~;~#AJ7g?8$jGK0lH8SKIprSJ-^j-W`I4i8<got<yZy)M-G<VevNJiWgo7T2YvrUbg4|=H@B~>=<t?cL2oYbhDvz2eQ?Wh`e7jacx*4ibLrSfmtXe$0gdlQ2Yo^#>cv$0@bU3(^V9nA@h^ZKD8-G~B^EXuynXT11BK)<ro)yD2`+8)BiT2i^!QmiZiZnvhp+k}B_oQ#f=-)b8BJ4rV+v7um=O<Vb*+!xhutNeKTd;Tw|DGh8)7c%z{q2lzcC+y;wp&xZGHXR%&LutK0P<I67g*BEy6z&sMF5lDmdTK*l|DNOkXQ%b!FQ$C$dyx^q}2oFR%K%5g#8=x`YX|EB-NczcYNLa<4D|VsZ;^9v<$$q^Uq7>gA6wGxYg@d?Q2x_rAClt}D}r&f%ms+%iT^7{nHt4{CG)$VTjTa^xYeL1)0w0a-tzZ~4(NFp~IExojm=s4IY~J05*Zqc-lF0#_24+I%X*kLyBM5i}8?nEOu^unvKK6aEpf7`wNEF#_$JqZ4g@HdOWk8*B8*92s!_w8-u}_FUsp0oP(?r5?)|x~k-$+CejjxWKU4DmSiRj;L*M9fwks*-ZQ8(olAGz3~nMl;P<{#%jFEc4j~bC^aX8uQPLv!vyLH0=)A)?f1N#5iO_dl3c`$o-)gM^(;k{2Ta#HPwSO21p$8DMWbMQT4O?m9j&{3AIG!UQ>Jy=zPCL##JT7TwOi&kZXLVlbz?ESZi9vxw=&p-?GZrkebA!W--;Qo%qB=blpI9R->_4~4wE^qbkjHL$aGH+J!Gm=j$MG>X0{u%F?X*?0ZWhW*ABt%Y@MepoDYgYf^P1`5#(@p?cHF#%a1Lla{#mA*stsf9#>x}rbWhnM?d-Q7JCtv)XbE}*WNhrXO>4%NQR)s&hC#rl)D-$ZntTtIBsOvZ+|O<Q8OVS(P*T6P;4J;--;<irRcZ^9fG5Ae;mJD%s;=o|MSbri`=31mwC=y59<B0rJvuoSmrx*$*=%>D#7BiVFB*M=rc$tw_wGAtu4sGSbn7$C=!x2k15~;j^;fbb828UFh|SU^jxsoSng(WdSv8G&+{a0R|pU`V|kGyqAlNIBKw7nR^(%~t;7drA5;$J9XJ_mcLC9|_5sDnXv<dxE{lka#C}Z9ef4nU)~aR>oa67+5DYM8U>*w}s`=W~lRQQ1*Z~;xyNh6i(jYhxXd{5TEIU(<KC$gd95hK9P_sL=En&=>g+5d<k~i=ESyn^?^d|yfR3M{lHG1wX!)g5g(aZ2R0G;k6&+aIpL<2YDgT9--if(@LJ53Dg82&r3RWkRTP;b4ErtZz>LAu8D(VY4o_r7ryV9pOVNM%P?{$Xz(BXjfHHM~dS+m$q~C*|zVLq^#OFDhVR0q1BP#=~g<mWGE3Yi&jFiPWv1-lvECFVhQo%ub26(asu{CR580-D>G@sN}VRgNnT?fjtE;d<>U>@}8LFRttN8%}~j6mR#=EhX$4^*^-064Jk?LPVi~L-$WG=owOZ6(k!V+@_&J;2f7&lsxxs}SqrUMsst=sgSAfk<J<h$Ew-0{$X)1l4s!hrAxsGwrhSpcv|SZ7yc0AFm~ca0dCJi`S*yO$!5U5m7$amenlDgmm7MS=LkVS<I;ZJ;y>LC@&s4(ob+t4ZjwprgsflNb;sh(}`l(NuSm};D=tm)pf|b!H7g=>BEA&smc9odpFhYu+(XA~2=^Kep9aHf`52hHrA+J&s@Uq;_Vv1MmPlExPzC?`n_GX8vk7iAQVR@xY*%T1IbqOg@EJ<^TX*ijz!~m(+N$lXo**w!Gg8!Vhx266R17)}wP(mye&&peS(*{B=pY&URah&<OZNCANR%-uM2#GEhhH1f8G2=;qdEvQ%a<>e8&J43Rsx1d47e}qHgNG)aqdao4k#IPKTfU9p(k^5Z7niMET;}VM;li_lxJo8>!wwNZkCtcjN;pI`G#T6`<}BjHL6&PerHf8~3HWrVjj6R1)vr`nY_50;lEK(~Y%~KZ?1AJ^olBS`$rix-rezM2BZbw(3{ByDvGw)KLk^1oD{5p1d~!gtz6uT!S}FKh9A!|-_OhH-!NHqvCB-7DDQtP?M<;9SvjZsMU5u3r8Q2nu!;mQf-lqWMFyui_7N3q(MZQR8V{|8uc+Wjh|7dvfdI4!=+1X)su#nPj6e8Iz%Y-+}+Pj`WpKw#(JXL_C6#4`1FbUyuj(QhU12LGDY;KKD5Ru3d^MD!EfVU(i6VMgkm_+8{(UFD5SU$KEPPIOY0dX+)=Ca|g{P=a#rgO1n<7s<x_aLLD_lq3u16DGF-qj{yJFB{^h=ax#w9-08)*^a{;o*N??9wK#SU{mp0L8`qF5PfRSE!6xw$MQ9DH@`b*r=upQK%5SSXoT%ZyXUjvP#5bkqgS9zYbg~N(EJ}ZWn(|?-Tmfu$4nYet=UY0<$%}Lprn+xX+a$f}an$rG~3pNU)F~F5M61bckY%1Y>qzPTO;nU^mAHX8=m$W__>g+C;m131!MSoEjNnF&Pm_N=%J1LqZ~LjIyRP<mW*3t2R4XBf7@|Rz^jiB}1?(>S>I1!ej~zJW$p#zJ01tr6?Z5==1Zh1WkA&*+3_CaerfwbTzP}<+LJ&vSls07LX8~FXrlslenyKU#PU8l+jq3Gvtq@ResfsA?#Y$rjdp(Gy0XHT~qZQS@e~8>CD%1Sz^nliYulCi3L%h5yME`4N&+m@q3-BL(Ex9{W%GnRXjW)H(V&dL_rwwJJF>JR-%R|(YDt;&v2FdTZpyL@$xm|-%;9Ip5{?YRw&UVlsFIY2?ie_MugNp*N=WqaK4^WBB*D*LX@lT#o0a?6{2;mA+1@<W)2a8g4?}!19yKa2H0iWs)D;p*%6t98i3(C>Hc7TcbhnKR;zLbCH_JuIMc2YG^+eNiI(<!`Yb}C>W#r^*MwAZQcUVSxS0f&P-FU1B<+`$0#fBJXtO=edi%Ew4lxpV3Tl&ZjWV``ombMM)2Qk4^H0)L7v|JiRUXxEh_V9BNTVJ@{IkwU<dUV##gSOO6+$(_8t9m$RE5s+V9H(+ua+=XslTMb)>xlDUx;)??0ZEecF29g{CgIQj0sl=ADI0&9|6$9ym{GLyeOjXjR>S~)~e2lE0a>u>g;R{AX@p&YF*=Ap%a=rkfn5tOmI*>O!%!zab>NMwW#=Q;JaV8zWd_q`R+Vx0qxX*e))cBBHgwSRp_c@3jC}#j0lrgvsiPlZ(YnED2G^;8S2)X*c3<1V=pjwtUNwS-7>vcNQ%_R!RMQr4kC4~wlwR5)W=uPL;LbgW@1e0F?ag0+3G{A@A$CLW!@z|J<CYaI0XY$R!G=4o3}ny4Utn{7;@3|rn>tTZw(AOyag1_F6*#b2}aE!37sCZ8U$Wo*rStb@#IN$#DX?Tx(-3rSSVSc02IrWQ_pJ+cQSdg9sRp70{+IFj~fGuI}j>*=y(@xw5g#woeZ9x<K}=U9&bSnrpB!v%muy(B=^6Ih^6BOoit#Hc17Yg4NBWSLM&4%ZkC(vDv6kU$Oc=uERCWs0<RbZp6Wbpc%N0W>N_dM?aDbU`}Zu9VT}L8TGu$gX$?Rm2=mHFr|ji}Pv;#Q0eMuY;!#RI30RaYfQH$3qKlWBGS?2rGC!dt-=|WrUBu{bo(!He4YW~*Ftu)d?J{9|B(9cLltHW$FH4oZ>Qfr@EJ3Z8d7}@s)L!tH3R&BW%Z7fTcmZlkj~a`ct$5fRE5Ej|Y)Bk9AxLV8tci$$D4ZyGeu~0m_D6i?lOtzv%QcpFa`;eQKwYSEQF6Yuw2nkbxPvf^dU7F^wz4G}iD{F{9FFNndj*JFQ^Kkkub&21tKHG!{EQAuAQy7>57VYy_6tqOC6ts@8=mn}Ux=6W^oQqSm-~NNK%COyw-1Oo5=ZS=S9Qnb4du~KB>+JaZ@<-8e2q3gCMsWd62`>iGe24nm>(xdua`CGVukwg`Lq>-aUW%VTd}D@l8&9ReBl14p%)|5S&P!^A#ZeJ(`&X6fM=2IYHo^Bu3n17tAdTF7MUCsQi#Uj1&0eqGBu7PJZFj%GNplT*i(>AR{pcHfLLWn;#4KYHXP|B1qPs+ki`9|1o$O0){co3lyfyy3|btN1>H$S)so2-u`>z_S3|*Clw8wP7^Y*u7}=6szebQx7a3>=pM<p_8yZK~M~oAZDRqIjT(Pk*jg)dVM9b}%-0R5STYWv}4iKBaD#ZYhXJw87xrjzk3TPZom*4IrM^wB+cx&lj@}OLS!znwA+1~{R8>9aHdD!D6?lL<S9KdoQUya<w+19sD1>ZF_pCgAP>lj>;a|>3%0!!X74YiAmddVBh7G526SKREw_UYaePa+*WV;Vc2Mkm!uK|LXHhs#33NZcjVMBvIz_VU5SA{FRAP<r>6s3w64R55^nxxzq>A#qLPjAqA~NDWaVQ|NI$l?AUG4#~ox!q7a701l(%fp#lS{&U{J>#jLVqPkMCmFxf>Giz7Xn7gDZh!nFGht--YDP*mYJG4}da23+MHR1rN$E&%Yz_3irDtIoYGI5EoQim?<Z1c2?=fdg{Y?RKf)nkPWW8TMA?=(q#5YoMfZIL(q${KSik;dvm4>hf09}zhLpkmO<HMHLV`b2ySh<!UA?6q9QRZPi#{f2UImfwy<KdDV4YOV>G-jIYF3!E_mxU}SBG3!QFQ#jZEd%xQJDYX4JYMp|?N(xpgP9gPPR+gjv>MRA2=`c`#D+Oqi+NT3c1fWk5dR5xVk|5;tM7}MR5@22i9$8}&#M{=&p%GanV&%=D)O@8X0nW-wtmAwlrk^d}u2j2#*HMttgJ`{U71p{oa%jW_aiCn+v`p9$_A*jyr`zdSsK>|*BA99+Jqv;b=iSv7_|C>DE9(5kM5|+ABPwtx)T=Z_4?6m_s!t<DJ!tL^%{PIzWi2B^0e@Q8Tq_OBQ18JC{5?*2d-Bs1n2zcP!#n8kWN25KWQr5dRNfI9Qxpn%X0U!wHIQnbhSn_k7Pb<rdqL}0^1dQi_*wjoKD2V?x35U1)keY&-msD@YJA1CpZyi{ZB)xZHW4RAt4ynl;b2%sS(A|h=zhwGMSuY)+2Mu<Y&gy`t*1nMSsKgAQZ=o!&$14O0p|Stx-}MNrC6psSI9^=mMEIYSBMW_SPKkb69h+CrSSxGbG-{;bCOleYS4@Flo|wScJd2fW4RP&k)5W6!mgZprh!d)U*pMJ)|dhkJ5uF-aQjN`<W=7~q@*v^1axxs#9ojEN9(4j+lf9y2FY};EjpP}#=Pbp`YKDxAuVORMaOjn{?K8so?<--jvIxXsn#^{og3kt<+)fymxfl=rNwFs+ZDJlGzUaWRLsjF^?`?08ecK<kxUG`=Y~*~lg#0@%^f=4RCK`c3L#rsc)~gz2i%h5iLJDRDkhPUY>}DTF$F5p#5HOZIu)uVGeGI6&a>32NNKfj(r%ZR-o+q(*u|>|id(W`HQ#$>n!&0#*yz*C)uaaB0FGFO52RR=;S(C#%nbgbG>ReRT)V63=Bnvlwc50uhO4G?qQ>V~0&D!xYcLbsQW7J#(=|Sp76h{k(K<Tf-8EW}Dl_59M6R61IjM=l0B#ruhmy38tgVVV48w{Tq8a5gY3x)V(7ZG*D#<5NcPMqCbr0vNf}A_KfV6puva8>E0uIpxSl9}hIL8P&s*Coj1`#o}SZT@NZCQf4m;Ig?Mcp|B#FNPi;faf<0<)QGLPXnvqL%0wE2KjK>s~zoDU%{NT*G~>I#-t#<dtcii%P(ZL{rQknoFwYS!zi}D*6=N2Zq4ZsZk_?eX&{CvR|HKX)9++<FG_g-gxfj&l;-(gX!T7wVfLl&`rt~?aUX|!5m2u&1Ik|0uVj<ey_y7h(c<N1{rd6TPAA=brp<?K7JNgYM#~!gDjLE*pyN(jB2++*lKk=ZLb52iDZC?xX`$|U`i6DtmtLbz38bAhBD&2b-bM7W*sH56<s8_Sp2kA1wPYLN3~otrjFbCChJ5tSXP87L?IVOq9VL^R9G|7+m+W{A^VJ_07d&2NG`2;k!3JC5V%lW6<NiGB{eFR>bXo%&`ShYNNkG|hYcPTN!@0-mNtu+cLd6p;pE;JS(6)2lq@UcOtiQvvw11ZCdsPgqHBy^qR)5bV6kS?DupK(;so2)(KQ<4sJ4<}7e*O0KDlbHbp~aeiZslC2quY!HzYfqS%tgeG#Vn~(?m!tB6YY76#`Nc|LGI)OJu38OGTrE5+HfS_&Q%T+KYV}V<y>3s#P#VfbrVdY+i|H<wLmANtdEkH*_zCP@N}%cJ9@GOZ$6c^!LK4eyFICZBuOJjcISbOHVgn8+RHBQN;fWRNoQmVl9mKk5e;kJWcFCJ|ZWIg&CG7=ZU2X=?-jmTFO|ZCfm2o3p;{b{ny}#rM1b?4Mg?pWD=M}il8hoRUtTGdD}ojE#+2U`IL@AC6~rz5Dy@ZRgkJ8&CMi`t(6fKipg3Y-)azfjDD34sY_eB97P!m&=E`}OgM)QcDw3hjU_CXRDMb-6z_*K7<bH7jPVQb`HJaR{mijUy`Aby=|meN<+Cd2CRV&Bt+OhO49)`8WX>qbEUf>c)S)XSuHV#j6*x3H6QP^4mK^$zQ26e+N=6E^Y3I_D#<J*ubc6LwsY+G@SPmByq;_xn^X)(ZBd)Cj-^WnX_)L^pscG5K6&kAZeLnmiA9~gE^_f;Wo?L0|BB!E%g;K)BF1`$<%*O-bWZ-yhb6Hzn+B7#bpd`lGmrRGP3RYf@WxZW0thdGY#BKw<yy$9wKkJQC$&OsXG9fOxe77T&tvnj#?Ra%8zZT<dY#B>UXkGDqIbkUU4E2ibwld0X$q$wwGl!wbRDF#Eq@1cFR)A}ktz7nj(;@iijB!{*XBn=^Ap1b43Le;lja9HLRpH6mb*$*6$gWdKAU!HX5$|CMh&uT^69Q;B&pH*?DQq!@&SUIiC6kaknD(b}@WOnmR|YbaP$q5D#i*XrU5s-fKt_aTmnv7HSqpL$$8_}?&?$?AW;&N(R%zmQc<}Zie#?>~enxGLVgKY2Gu8GYfiPW>ZI2SVktp*O(hdkBKlGZ>>2)+CTdY{hpuKS&T*<t<WrcUA))}FyveY~4EzDYDOL8gt7Ws<T_XO9owa=_oTLyG<a$dsgA~2^~P3r_BvPT6|qmi#j4W>8va`kRs))#`(YgOe&EHnY0(rslNz>`NWMtTdZyKffmJbB$wUw~vIKx}xbufKxIoQ`w!mS4De@=}0Vz0s=DT%uuR677^arDAOWB}K{r-zpSHQin8KEonrbi*|KZ8<j0rNi16$J%Y)!zOAWp&kDNGxUu1sBJFqWrqtM#*1}`HMM|Azz@C_2pr-{g?xUcSbcAI`)gP%kxhm<9t~0Y7X9luXXm<I?Np&?j<%+APhn{b04PKN}#y~7n<SnRGU(~`ijlF`l?X=~(q$r<?tPF%JrEbZpp{<r;^WwENF0L0f1O|o(`3X&l;yM?U_}HLJEo8T;BBS0ssVD|FLOV-S5mYMxg?NYs$_b+Ata?J4b0X2rsH&E)V{f#dQ3TgYvDhuxmU9iuOys3^GUV#68bp30#$Ctt%LYWWa+ueF5W#m-m9nL@ov2QwFMFnd$Zf6C6Y{|XM1>hmy=5mig_@IUskZ{#>oAmYEW($VH`ghD9<@njZzVL6UjMEoWikANB@3#>3*hEUl~^nSmbVVT38Sj3SHStJKI#={B={RV8Rax#wJR4SlF~=E%9?5*n6aR1G?|J+(M7AuOLC>DXXHp0d5-0IBa2gBYKbnAB8Ofoomx_z^CZcL$*mMt71aXO*}JJM%P@;bO=T%=D^Yu_8mn!WDbu<R>OKkCNw#E*b&j^82G0|L7Hm63;KXTvgfb5&W`3_8+4G|=>m(bJPRL~UNjjFaY3rIitFA3e;hT1^YIQ{j9jCia_45QT<O%M?=h$(@1_R(b2yu9J24z@bX>R5^1qq{XiFp5HyjVJAZ>iJsI7@6ev5s;9;~maYF%^pTv}4y1`DN+td@Cn&Q5qv9_Qn3jBj3g%d36+ZL#ChU>-yO7lGTXaKNy0X?z-)giq_?KmV)|n)0j=~$PZ!Zn$y$;_+?UuVUa&pQHU$h4cZTBekUNXv4SajteJhN3cAS@wgS7P$Qdh<<@(5UHTr_iAIp^1)dB}Ohzzt;z#Q{1rY^W03;i=JbJ26mq!oXPQ=pOC)X-oJPC<FHg5IA6<ZFU2X~N*G!I4RG#L{#!CC`QR<2tOIq#t4i^F`IZ&1}PgYWixa0}bi7WBjX9CJp0CPUs6n{7x8%T3DiLjjJa;BABgXwLAsr4pZ_p2bw3ZP(B{?Dbj{sn5=aMJuB&uD&#4hH;xWeCa`BZrmcqC1ijFU=9U*doF=WZgK}T>Dn4B}xn12NZgy&;H?x$K>x53E!Vn}KInf;9^ioQ+>&|M^(;HWousxpxO5UW38S(xd3@_@dSez;jCy|jUQ9WBM{V;oP_%;XY9|*efr5@=}(sj_C-Kd;lwdBUj2;K!3$P&SA7vCYacCgMa@RB@@;+vFlqZ9sMgA_z66+okzE-8KjT~*OLVo0T>++!)f5dmAbG%J&{H|s|Bm382oB05+YB8BDK5~QZYpy?H;8&b`$P49FAvpi#p-4l7pWnth7dUBuxD<*o{E@!f3$lUZNd?kcn(LNFx!bUy5MF~2kh8@j%nYMgJGw|kQ`BX_5%*zAF*qkT)o$sTiQ@m75F_QUzVzk+`4Yk@ZG#N}fxI7^1+OV8p7CgZXlR<3-EUktTc03SVAV?q;rkht{v6`qA8_*T+oIRQw8P_S%FSt$<T`?*yljyW7n7CVtQvsHUNTi>~&0)3?XNd|TQGzA|6XS!l(0qYx1=a-NOg7aS;h7Sj{MN1@%O?|-@PJ9g{RsJjwUo1Q`eaOZBQJ)fR!iAbZ(pY%XiMhX)O3=(Wp-3VDVEDxVtYOVWroxdXeZ&Q8KnJ;tz};(X=GoELj5(QL*_MsHO&lCiYN%6(uJX7+O6tUWK9jJDxd;!x;hziglqYuyfUAt6vIg{+J@3(7E+`z!#|SHvr(UJ6PHlVtM!T{+w_dMbgi-DX+y}C`5?8ci@MrWyQ^hv@U(zpLb|Rpo~b-lDh;dja8cO`DvnqU%KdY_ASc~`p2{1q_hJPNm|tMw@6-h5PQ6<JS8x+Gwn(kW4l8kDByUA61@o;L*-7GLylJfFvFm7K>=m(q>X`9M1k$7ez%dr@w-IxfFwqzhHfF`wU}3gdowv?O-aFjQiw=lJEj^+A5A(nE#`)O0dOq||>Dcy+nM>+(U(-@~Q#TpaKWS+feX2wW6O-S5$nC1rJt(RnMB|mzmZX?vdRv9%_LP?=V@(O8iOziXYIdb0@u!U4nk({9yCqXZ<TUow;LME@Q7%*0eMpBM9_wPtX;K$de>b?`0%EIDk5nLYkvodrv4eYyhn&2&a-@*Q@sTw;yK!zppzRnKGaewJyotQB;=s0VlB%rr_LOK-lEO7zJq6*YM5@%UOA2~Q4?m?y&uROrQ}X)z8n=?X_RZtN`@^@sd^7pL`wD*c{1r<VH#qcyep0*Z+D_~~?0!7^CXEk*wjG8H8zXpYKtKKc>Hh$n7D$l')).decode('utf-8'))
_ACTIONS_6C8S_3Q = json.loads(zlib.decompress(base64.b85decode('c-rk<U2j`ia{MoP)`Lk=UwPBm+}K#n$dK(2n}IMGAR7b-HV>1$1^eIQSR#3OPjz)wpF`SS_{juC-+R7KcXf63um5}Y@4x@?x4-^z_D{c_{q*VG{hQz3-+lP_>2ZDbbbj_9zyH_2{rBg;eE#^i-~af}zy8nX&%d6%efQ<B+J~P${pGj2U*7$EcYk(%_WEIScD`)B{_u9aen0uchxPi+=dU+!*LNS!&aY=*|Gd6`_~q<;vHSV^$A>qcUVq&GkE^Grzn@P#_Ws@LKYx0^f74>pw_ndT>kl8lwDp&V$B%EneA<0A`*1iAAJ+Hx`?p@q-@1L=<W-;{)7S1l&8Gr2VD`Fj_FxZpE%`Dhi-W$t{EEEm{r%nRbu^x+KimHR-ZpDDdF#u6nT}`EjxXQ+vR@1beSMj!;AiOwukYsX-!G55kL$<zBAS19xO(8yUCtNLhlfw|Mbs|NKmGsCIQVAPJ2sW=;2aL{Y?Su>dwut^G`Bx`-kFoGTXVS|uJ)zdQJDTJoi4Ed(By!f(5ztcmY1;yV>TI%X2#mz=ri^*?sVu5o;%-p`yp(nDOi^a;cx?+Av{|7*>cbYZDi4*lTY5ZrTSRP-{kWMhVbQt0dthin?8uUckDiVK6^i)58lA-$GzvlFTbRdKKA)^!iRKV`+p~I8v5My!&i9h>{hu5tjXjsH7<}bPo1Bw&h|Zd3+DC+`DtTDjA_B^hx_~W>yN+vY5n-|-Tk|NJv<Wz4PN;r#u6#N<4AL`y|pLp3HQ*>5t;osxXLe|3=8m^UjN4Y&ilBkd$+0m*J+ag^R6);Cq_6}xD`JG7$a~`;9k8fZOcsNeVFz(>ti~Az_B+BQs%0_PuT<6SfEeo1DQu4+K(OnXx!wY0~HUdWcw-`i2COF{1Z>7&-GP+r}S~qTQ-~rVBGH?*&2iS=5K)$Vq50zvmTe4ssuMXv0?q=Y2%+J-}}IZT44Zt(Pb1MAXzju*u~a&#W6G|xSdn$pl}UlhCnA&CtVCf3<QKThL=Y1Ze-y4{<!WN74S0W(bQM~Z;9qVy%97UqGX<s;o(+W{%8tN131kB013`TM`XwW4Oi*VlYfq-{o^2KKOXzzu_h)JTQ7F39t6{asC;5+T~^M_iZ5=0BSn|b07Lqshnd|~F;F~6$!R|ciT8S;>`o8H=I!0%zeFAD1&k)$(OrEp1dWDj*O%fDO~;~#AJ7g?8$jGK0lH8SKIprSJ-^j-W`I4i8<got<yZy)M-G<VevNJiWgo7T2YvrUbg4|=H@B~>=<t?cL2oYbhDvz2eQ?Wh`e7jacx*4ibLrSfmtXe$0gdlQ2Yo^#>cv$0@bU3(^V9nA@h^ZKD8-G~B^EXuynXT11BK)<ro)yD2`+8)BiT2i^!QmiZiZnvhp+k}B_oQ#f=-)b8BJ4rV+v7um=O<Vb*+!xhutNeKTd;Tw|DGh8)7c%z{q2lzcC+y;wp&xZGHXR%&LutK0P<I67g*BEy6z&sMF5lDmdTK*l|DNOkXQ%b!FQ$C$dyx^q}2oFR%K%5g#8=x`YX|EB-NczcYNLa<4D|VsZ;^9v<$$q^Uq7>gA6wGxYg@d?Q2x_rAClt}D}r&f%ms+%iT^7{nHt4{CG)$VTjTa^xYeL1)0w0a-tzZ~4(NFp~IExojm=s4IY~J05*Zqc-lF0#_24+I%X*kLyBM5i}8?nEOu^unvKK6aEpf7`wNEF#_$JqZ4g@HdOWk8*B8*92s!_w8-u}_FUsp0oP(?r5?)|x~k-$+CejjxWKU4DmSiRj;L*M9fwks*-ZQ8(olAGz3~nMl;P<{#%jFEc4j~bC^aX8uQPLv!vyLH0=)A)?f1N#5iO_dl3c`$o-)gM^(;k{2Ta#HPwSO21p$8DMWbMQT4O?m9j&{3AIG!UQ>Jy=zPCL##JT7TwOi&kZXLVlbz?ESZi9vxw=&p-?GZrkebA!W--;Qo%qB=blpI9R->_4~4wE^qbkjHL$aGH+J!Gm=j$MG>X0{u%F?X*?0ZWhW*ABt%Y@MepoDYgYf^P1`5#(@p?cHF#%a1Lla{#mA*stsf9#>x}rbWhnM?d-Q7JCtv)XbE}*WNhrXO>4%NQR)s&hC#rl)D-$ZntTtIBsOvZ+|O<Q8OVS(P*T6P;4J;--;<irRcZ^9fG5Ae;mJD%s;=o|MSbri`=31mwC=y59<B0rJvuoSmrx*$*=%>D#7BiVFB*M=rc$tw_wGAtu4sGSbn7$C=!x2k15~;j^;fbb828UFh|SU^jxsoSng(WdSv8G&+{a0R|pU`V|kGyqAlNIBKw7nR^(%~t;7drA5;$J9XJ_mcLC9|_5sDnXv<dxE{lka#C}Z9ef4nU)~aR>oa67+5DYM8U>*w}s`=W~lRQQ1*Z~;xyNh6i(jYhxXd{5TEIU(<KC$gd95hK9P_sL=En&=>g+5d<k~i=ESyn^?^d|yfR3M{lHG1wX!)g5g(aZ2R0G;k6&+aH;Mgy-!2z^I=72W;hcbXj3F+6x+tz-^7A>VpIP2Hc*!*q@Dqq+4x4u0b*z^or^lFF{G{KMW%M&{_ZYnb~v<N8w006k=tt?;q}Ru*uO)_F`kG5byK+KQkQsdGQQRS!p?Ofuw=J0<2uJ8RgREfo_BaZ~qNIwC6ht>Cy~?@HiL!5bgLDWLo(CcVYsk1k0T$@y-*X<)OGZ8-?$kkX~@1n(C7P1F<7>Dv)F&C-h`PZ$_|po{UZI#ZaHwa^-<O6amRUF!ruzR{1}VtWaQEQVe;Ay?860+x_#+81L?+f~uUJ3+I6DL3SmryQ-5wdxxktl_kPF_Jc;nFF;}$*F%bs8DvTbHdKo3)~YXO(k$&*G-dQiBbTcns}x>PO!4BpZYY4mF~!ceiZ5`SQ&l7kyUrHLIef8SBXOoW2NXB-6{i+$dUNfF)2UvV2WWJ@+vhIFU#^QCVRCWH5j1jOT@TuZ=RU?Xx0=MpjQf(O@ZNCmzn})lQfr@2A0W63^040&JJFj%`<Hx_|Iv3TM|$)WQLmo#l%7xt-Q52ZAj$uNxuac+nKN1_8Ty1rS@Niu;^l8m=<gmGsXm%7oH_3cgsNN%z%5N-*QlVan$-ccxci&$|x5b35P?t<=a>;?LszjaRJN4WxgI6GCUiIt7LLF><|G&X?aGkghNEblfi9b&LUnMWVxnOy6E(mfKP|om|9CwB};Y1=GvzqEsV{_Ml+zo9!L(=xr9lQyaBv#S`HyOQdo7&&=k%WTVKCC<gf^^qDFSWCkJ%vtKcA^HG`jJQU)b&FUtuQ9K88fk}aa@!j^Y_bkfE?Phdp6T*$?i$Q*`X3GhAzAcr9ja@zQGq$)y2GAE-ug~WUAfeuI$GS*8;E6dIfw1b6|cB2r<Zn-ABS=Qe5r22%L`sS$uB&E<FaED0<m$TKoxEhGdtmJiTe1eEfmY4_3s0QpMDXoC6_{JnM7mtoCG{*A5rEseCQ4ENKu{W0ucjd>gn>MkFEgMhele-5QNxfh0XdkeWx%93|3ENrKWknn`zMz%XF}fB}Mhp-C^J14aaqR*Mbpj|Z?sw^iOS(b@&9a3CT2IjsrPxL_afm{N;Kj;fYJcO%*^yNu9*bOB4*hlDQc-HDa-F;QYkHs1uZFE08uA02DiN5iDIe0IrNDiz84>(^$SpNo=R$&o1exi6D5panV<Z@}`*PZzn*_T#J~#tV8aMxYT~{gE-AgEA#^Kb+2#d*xNK#{Jlo=8dX=9W%#UVczs$aj^$sEx=7O*lZN-Y_JRnbvntP>_!VBmqWqVerhg(^ky7)GC;e<i5H8_5Pbsf+s?gG8)>9WAF8DU>a1(Y1ht=zK9(SDeIUh5JH92Bpl#%A6s8EUove<_uxix;Bk8e3{X&6cwAQ_sF8J%u8p!mdg@bK2=;XEl4cL1C1C)>TZA%fQjGh)E{EbQtHo1*sS8=2|40IDJBZSh~J4WU9b{0M2WV&?s<l*+}}d1g^ri65&w?T-tsh$TCzg1CZX7QfKM>^2r(k0_PKuabCUD*loCNb>lLD0eJ{@T$*2&mYYl15T0V1#5ER_*y&JguQ!&6U+g26aRmzUY#MA%`*GcyW^Sj%`nX_7zG$`>GI>DKCm7r1O-$}Hz=hJ5q5>;;uPP-<kl9OUm@4?L^up}GPmm-nBv?!1&c|n`)an{?vWpId*z*Eqjglm+sCG5PC9>qpYp`U+}rn)ev&Z_dLenXTMXhs_K7~-FGP9hgCWiF1y>a7r}5!OJ*B&8~J77A1Ll6bX*sY?CD4YtPm^!Y-hD`MX(da*<96XxHuSY%ANLioV!zxfD&7Us<h*y2SIb#Fu<eX~||PF$IkifU(PYXH&8Z&vFX_X?fR+<`2mV`PGZ@?pYnRmv=DjjTn*Zv)@`vi02;U(a{vSqo^V4)n|SOA~3gg{VSTO;g}!wP8e<yqd+DdwuI-{y;gzs?1Qg-o&OjVjg>exnt$=Q7V|}WkXV=Mh-sT)U*((bG4;eAEZ9MdLG)BZ!!~OQkl8akIhyeVtvPlg)aCm@#$GclEx_*sIo%BzS+F>scMLv`ofTlt~XWSuXt-<(BUnhaCTXT)tWGB4oT?rm~|oW0>d7iRFx-Bsv{P(QQUP1s>VXe3I(88xSV=kYq*oii|y#&g%R*K=6u{3P~3q~(L=|(XroOH)#+sL>>M`-MDchFYA`i!^<XaWMIgTaT|_J$H|V4ROSCHzw`ow?_7P&4Qkk>dY*$Id<U=;t!ewcce-U`aAn;V@X~X-hl2zYHF>Y7RVFAErnG9q6C)T>g`Aw?<B0-o}Mml9LAACCR*a*m@LKTlv@=3s=WC1kHz7t)%)Reh)IF|VdCHX#;((NKffAeJUq-mgyI)tfp>uZ+@+aqzcw6Y9h#duk&>{XxApl1ncz04bZpr!VLzf{QDUR*Zx3&jgiQ+m``+-$|e=2-c)g=ItHzzIQ8OJq$%3`F5X!ShoTCbK`{GoKtegIlh#ypzL+@&f8Ym5Y+|t)+D&Lc$${Vbqfgsl=5n(MU|2ROWC@KiVrm+?o<r#d!TRuv+bo7UySlSOU3_vwxU2?Xq8JLN21Dq}uR|m-<4ytfxObm%ZHo%L3w*4!?as#F02^$GYk~E^jE0ekuV7nt1!I#^P(V`7u%Xx|1*_9-sNqdcgcRL3+KcK^H63kI$#A7>xTU^V^C|4U%;1jO7FOKMlPYna*02UJrSr8=GFUg#bK@Y*%wrl*08=BwiJ4M77A|sE|T51}`{VIFhMx9N{@roRBFEbi<y4Y_js7l?B8qLlUPdDYoHACn+!h)r2JOPbI)FnXz_Eq@bLup<>YDpe*Q4Dyo)Du85scShyMr)}rK^rou2C1IEaf<oY#&e7eX$JNP851=-Lzx;|o@h)k&qyyc3Gg=wUet07u$$K+l|{@&{AId_2A{8cFifIKU649G<^f>J=^aJu|<Cpn_x9l~2n|B?sg3LH+^Va)z6IM^8V@6W>?FL9UIso(&X1Nmy?F3z^TeJc2_srei^Bw5GclAK$x3Km%MhH0o>WYkOEShn!$pu6H`AGS~To_G@J;2G1{@iaQARto9~i91{t5=P=Kp(X-XZnBpTE*7ak|AErG$3!&=OrVMZ1k4o%atw)U8fP>+&O~a68ks_m>!~bw-Ec@21{H?pVFYj(B@eV)aq^$@4qkW7SrXNiimhY^@R(V<s>a+URY9bftvIaKR7oLgjohK7YJ{th?yV6ANIhQ7{RD<(VphR(F_no+e3d$MS!bK4Wjq&Fk6@#8cC8*OWEk^4u6n0Q;)9UxMQn?_=~vd6ONlgA7ka2^9s7vL2>=y?R<5D_2GA$sTR`mF@nEmzDz0Km_Ukv4gR}g0B>G8h8c}mi!1RVB+*sg@5x}J-AB$NxvYNuV{@?r6=1-yRzftQH3|3OGQgI5Y_p-7a?N?_hfJ}#h`dcYLo76rXSRw#@iqNalPL>2Arzi4lsgwZoGVsV6lOW!<Rt}BGDiJGh4yEQRRS9rbR$?9J6EXd4`F5q+1-y=elpaLurK_;kwUI+3E{Fr=x~65qj<A=JT07lN&q6&$W)Q(t3+Y)9EI9A3w!n8bPFYdsFD6<Y3mZ{^L!n-!DSFV+uT^~-De6IUe`vl5v@L5H84CE*y5?GGScZBJR^ab(%G;BlroePmKN#LYhbKe3(j-%yc&74>(3ql7&@+Sed#Zs{`!uv>$+xhTSltU+zmoSA!NSktZ}g#+GrxUBGOacecJPLkTv6jIrv2=%m~W$62C|7bF<NC>T?_}qGRm5a6hQY=Ml1phK*<g_JYd6dmT5gD;>*%lR+g%1oqd*dI1Di7=hv;VFe}9}<+(yey0JvjM7~0N0K-~f0Gl8<!YYj?pquMm2%D3vVpfA*l&91nNVAh)_!`TlFpKOoEfjX;)H4li%KI8m-m=CNkl2wb_k-J4awo6))*&T*sV1P4t0(q?EI3*>Mcq#H88S$wb8XSdlrrWu_s~~aQVwY;<1IR_Bk+d~d-W9SNpRdK<V>}uiSOJ9=Pb{~BDyrRsxB>7TiC9^g`qhhTB2fJ7O4+Bw9@#BnU7>**gZFds+?pFuWjzo@us2!j#miT(!vwg={Vq)98YYeB~&qqjAV<<)Q%}oktVKDqtK~PEtvsIM|Ga1Rz*syg_Cx>y!0*x@xv}&MNr(56|4E)E7J^C#lc3OUalrJ_y%yqGJGJ#nhc-N&}L@v7o|}QDd*Z<O*dCf_o~&V?KE69of9=a#}ZiMhhBr3;FgjYxt*@@v9utVU5M7v5$~?if>fCaPbPBZG|ov)6b5j^I5?D~b!2T-)L|G_#1PFWpGjk<`he!8aZyP=iMm6n3$1%NR~6*k$pxg%OO##x))R1uCcwg0(8M`L&{18qS2c);sl`f525-v})V=KY#3<^{At0ViRtQgAJQbMDToWSN4ivRS$5<g93Rw5*0Z5q?!QmS2Yt^~Bv>>lc>s(X<W+a+o{?J@fHP2E@GE&i}=sqw6rcR9_5$uc2!j}E=97|g{QyPaQit@&DH-FYx9T-dxZ>a6uuz+q-wrFR*s1D{xifAqaO%Z_T$@hCD_C*v@V>HN+quVlBL#V4@RP^z)xKi`9P8ejN{J^G^a$!`v6~b1l<7s;xU`!+fM8t*0)df?MC}l-2qwYmdeK3>}->u{26gTTAiLK}&!NuaItt#-Do;s@KnlW|U);C!vvca+<Od$%nFcKBvy`#dKiQcZf?h4swECndqw?J}f&5JC9(Sg8);;P6hHY}-8u~g4xf`VQmxI$uElsIhgs7UHI%eAyw#JnR=z6>Y##>kr7c%o!kA!nk+Rhi98VKzxtB^O;|^b&o(D+h};n^q}2xezDVwvMjR5J$C@47)JOpz+C7bFDKd<5Z+!21GDPG`u0%>C7tJ6{pb<8J{LXViBpsWvCF4lK4-bh+iU0bzLeNC6oZkE5_IPs?lET(-<?!R#L5kAp(ro&SvvUJS!i<l}@@8t-7ImF@)+o3AA&s{#)AL8>7D$PW3}Yjcl7@D{oAD^Idwn`P#VCNQff-SD^ZiP#0@qynmdUY2#^P2l5d)Q7p``JULG+RY-SWv(r+>DmB@@ZC=<B<m$f$M=Y&Pj&2~TUni5mBvJ%rfvF0?3Cr6C5^5>8`pTzt6e_tiCWCkYajb$=6=`lJfo!des8CGS^7vMR$Yb=YbVyy=(&Z@1Sb&aTDq+Gobg<i1A8RaOxuo(_QlWT1oWZzbu40T|fX`P<zv^d>W$NuzUrHz17%87sK{v7DJ!zd)VPtR?s3vnpNoHaF7o`qeDRKR#rmMiA(U}O{oVDc8e}uw!$5k>?m`yvEo-~$42c#RUXG&GF8o+Y6pdht-+n;X-3K(&19r!+mn#O0M%t}qmj;_#9o$vGE_xRAOp0Cfe((&X<YZo~c{VS9bE_U%{C}ln#5GMo2Yn#j3^3tZcp#dc^&c0+iY*n!GaxClZQenL<z9)7Y=;cLM`}<jMoJw}&3YH0R$>qBpschxZC~wEBWBIihZ)3|?YC`LZ=gSF8DPX8qY`2wBZcBc!1erMuMW*U&Bp~Hf9kBvjvux$E51bCcM`w(~B09@(O$ONqI#uw%9&D_FWvL2J&aPucFGY5pN&@LoA&PhpOF-1g=a~>d!+F-JxK3e<F?1ed7b}^B)WNhrje{5FQ@t{fp@cGNn=VH6l<s1j3js1BJiAo663tqWqd2Ck*MLr0Bs9~x1hYyLzr%yK5Aj=;6!9}^YYh7*kC>^p7YT&vifnt7(2YcyuaI^?5c#3kj83nk8QEgRQU>jf>)=Y}-7PD;JGIUTRh6aQS#M$18e5V}(YMG~yuK&6o~?amt=cl6o0IbrUKfEm)oNNN7?C|Hm>P|IMQSj;!I!Id`?9_elwPYUH)5d)@RV*V;{cvKdNI;lVBLMQaOcVEj`{*58v$a&Q+@pvROWP?qqqFR&6Ae`%<7F+mF5x+E0bua)F~Bf11Kp{2KZK?K$1G7*=k86`dqZDv)ZU^xk_T$(&!OPruA)2m3vmug~p8yrxa<wYd59FuCx{&^DR>9ECcq$`~p2KkZ~UcounfyJF5Oj)yY*!hjg8p<v25twL-JYM^37%$thP{Jw5b%Q)}>|oH7PtnIdmNt@@%Cu4(KQv~8y?*Cj>yRAgl!Tq$)+Rt;^n6q^^Xt#NU^s39;gM95EQN)*?*pv1=pU1}k_O%)mS=1D~{xDnb}nu?%W0Vu>nEKp7mMQ7C$(wq~CZbntLd>wnE{fr{GR*J=L!M2=hSY{$Gy^|qVchw;B8!_%Wu3t7FqLstE4ulB4o2ry8rR_v@Dt*~A1w?LZm7b6fCLk)zXzDFHxhd3~R7<@T*j|UBjAIeL#Jssq`SYkvDtjxTk@Wg^Eh&rPA1ql=EnWaOU#i4n5wN^<08SWHUA+R%U-eP1KqJB5;K?Yb39DVXAd!?lvQ^ep1Hp_1U8BiV9EvVlRbG-SO+6z=vdD8R&l_2s@={B5krX-fQt8x^>YOJ@Moey{u&SsQsLtL^Wm$$<L~1Haaa)PnW7Sw~yG)tZbx`+7$WF2)TdZ@m6*YLC2()0^DFP=>`y-TjI5G2k^~jzdby+9bkaR*OyHC=wq)l7b<XLrXSqk5@dsV9|Lg+Z%b*i5ycp*=4CqBoHD>fJa-$97Ovok2e3QKb{*C|LCeM`jqC*#G^DSJzup2t~Y!-;j23mETkmWruRw5J`rj>s=dZ|7S%nTygGDX}m1Hy-&m7Rjrls2ei<OkdZ>j+d-P?Eb+J<aF0<msGSazq1t7mz&0HdPjZ;OV^yHF2FC7It+{av5G=mfo{-#Nb@@ZfsGYR(PPc*LsigCrmz**B}L9yi7eMgrmN8xbpBYTw5}F7$U$VFr2^)dhcR`*?O5oaVVR4bV<xTmQ=9^g+@^*GYj6t6lNI#-EFfPKd`S}qZw-!2nj@B`lPP&FtRL55<s|(OGng-`_HAYx4ph@uOC4xPza8UWl`?4<S8_sMAmVqzK-9t#Rcl;5=@G$f9joOjKzEpur#a9(d4=-vpihxD^ulDVGw4}Khg2a?>AZ1tpfZ6y(=lx|+$QLSUNpD7=;1VJl^vA(s#o#p!pZIG7ICvv8@-vOq+BO-A{B-p>Bx!Z2&b1)qFr}Zo1WgdvV`sV98mHmRm_O@?_hXQU&Z27aX5*LOo{5*V(Ew3d&9RmSpPuKjW6{`hmx*??(9b8467wKUPkaPxImT&ZoBvnv9*JBc7d1VX%ye2j2oTs2OFdyQmFtM&2&le6X>dn-VsA8E#)3d`HcwJx}{l}oV{5$vahTI-xSfo!VoDe-<BXXB?e8eK;4jPer<ZE8<^!8Q|z9|LoN#gSJ0CK9au5Z({?$NEkov}KjAAO1dH~O$PhN_@hwWwDK+e9*2}czGn#=nC(EZw!eCw=K*r`g;qQDOEuG?}T8fd({}ZFlrfsOzhM~z|(!u2cS=WZ;1he1?ZkP;eD`06gl(6H0-~vGcsW9EV5{uPDt=NFBc<1cV+{n02iGIO#n&^sAahXJ?UBSfNQk)8~L_{L}JZ=uNjW|nG5Q!2r8JHL!q=n`SWGk>H2xqdX&Ir$x_~f^C1zA3su!ILpBJM}X7p$e6jngM%x*K^hEVWw7rh5B21wmUf-=?OM<SnzKB1*Ab))L$E87MQPjzBvJN6jGZXKXF|GD#!*S`_N9AssTW39M;mkWxfJ0F^Eb71M52uOe$|NL2w9h||@{m?K=vALW(#M5P!`g3&gVCbN(tg&F>lgr1H1bep(@a$c=hEZL@K#HDME9ZwrVw#)~qU0u}GrrKRCV}qv!6cf^QmGMmFsZwcJrH6~kR#0)oYEbT<>jgRK2J}?kc)b@ZXu$je3xB63Fn8+R3b=xssIf(AMRr(;6C-&mYAKj+&B#s?C*w_HHIH3K8)L7C1ysk3Um}nu6#$O0c)yL9yM&3xh_Ep$z6J}k&FZ{$PV(O2ZeDaiG-~My?SGj6tvAlc-qrJ=e@e%;XUtqupZl7Y%A2~$sQyVyyXaFTN|>1Z_Cs!0o$f(V4Ivt@q_!l*EYsU6EVrk;JQ-_B7)^BMvsbe#C5b;}?ABb7huSTfA|j`;rv_(kl!$Vfy6!_d^zc|0Q%;k*p!&PP1s4!om3pKCnTy;}?2aAWTRi0CwUr}<JdTg7(b<i269R3=z?ks>3FS@Xl@$lJeUnsWt+%H{o01f+>FOy6M<r6FeqB<~Q+oI*MS4!#SDljA-`BX6<h5@eAKo9n_2rw%2i{lkv*)i^y12oi7xa_bUDtME_hI+r**9r?5VY+uWY`$NTLb#(?@#{+fyYZt')).decode('utf-8'))
_ACTIONS_6C12S_4Q_FIRST_YARN = json.loads(zlib.decompress(base64.b85decode('c-rk<%Wfn|a{L#bd0;(QBz5C-*J>Ke88%3^3ade3Fo0GNAgm4}-Gu#j^^*0-%CImu^N3`#N4yn^#msnzyScgfFaLY?@4x;2x4-^=_D{c@{qW_}-N#=)-#$Kld03xq&(HqjxBvRL|Ni=yuOI*R+wcGR*Z=wY`IoaFKRy3d`|!h;zx;ap^QWI~@6OK8KHP84&gaF~k3X*0p9g<<T(3WV{d)7``u6GU{A%>|PwTt;pU=)`ho66bxc~U&!_)CUR@?30&xalR{OQA=zkEKvX*THFFK3(e<I{6nf4+Zs`tkYG;j7Vy(}8$g-`ySGx){H8|G2@cKtqPFJ$@Qb1!}<Pb=BE}Jv_AJc}`|0eck<vyzBGb?T2-3JW+r4{{Y@LYBzc7?q7!ES+wK%yPuDX;iRv-nX3FO9O3ot`2EM_ar?A>7%!sncc-fdF5UTf5k202884!8asKHaJLBY=QSaDPmV<LTz@t$*_V2^(ZfWj+^s+MtUAN})I9%mR_oFcURXAN>|DnkNJE2&?<So0g2V*uEj$+2j-{>>88+ST%C(j-4yyFm-(^OfPGvROpo1uEN^0Vcn3);w{LnofReM|MRl)s7R5e(t(gaLCD&6_@mhj$!4d_8*~(Fbqfj^p0);N36jr1yP3o$xLl*#Ga~O<kWGe)tBD9o;I6iZvM=rp5)*=c(hf)!DwU-h#0`LVjA95q(<l;r{M!{o(1?Kdm30KHYu#*V8kh)8M6FVl0vLJ0_Zg{jEJ{PjwF+9FftFD_8mD*02EI^!hjEcihKi-n$L$zebw`n0JNwI55J&!p-;@z!-sh0{3dSv@J84_hH!EsE^?Q0>|DkNSUhwKSd8@V}U+}4`d#JXg@aiqxB{y9jN-CO17`Efv9gD&p+{W+FV}+cnTi}y=B9B0LK0Ck)<&hZ~hWEA+}}QKI?IzsY-COS2nEQpVt3r^1Tmis3iulXH7-{0+K~jgI#QGR~$ogDz|fJ9VD*7$Pj3R>ZFUIi-CY}#_FY!yc-#~emt(*Mg_dgc{DW^z*}nbAKnO>4UsZW$nbEhEq*iwr~#a20e}SOq9fAffQGBI>&ZXH(*8Ke+52PPA8TS#b?e2B)q`MqB`P0ST9=tKGvkY!;7HQtGr*9x=wW1cWegM#QgYf)LgKAnD7(`uWAo$f!@txz)(RL6x}&@LVh9=y)uAuRAsUWF3qPP7oHBrTU;;FuAbijd9ea7J>C6Co<S;11k&3Yl0FIn2yW<+&56UrIDG&PbiRe-pzHe+_S<&G=!Ghjg;0>AZaQWbp<MeJIyg#-T;kk5dq|4_$e?sHC)<K`D5w$aw9-kg=H$SW&9{vJ=bSZAcF0pFEmA6|^NE~B2ZAq8l(ndd$eIrVbpM~RQ7=~l`svS}?q8Kdbw3*6i8rmB}h|0r^crdGJeH=a<F6sDj8VtL?V+Y$1b5T1+9-I7)@dzYWL9O4`*DuY?+IZ;GOG7ge&+^_P{4;?%?L01n^G(K%dyg}HtEkn=wrLtHmBlu3d{WHd<W*lc;=}!uXOf`vRq>Ch`yJscnR|r+5QAHAbANyLoTdVesNElTGxYU<{3t{MkG{ASu1nL0&f%mMnKz7_(1|TF9@N?eARDp!$&rUV2b}>!2W0*9zU6zzz)0dt=CYMgp{4+;?s&8@jmo%h2wX{EYVj!zKduvDMbJcmVje$bz&Zr_4fsdEVr<?D#t4*ij!v}k*^t=_Y^>2Ib7a8zQzE<L*mI6Y1zd}fl{%F%w94e5+Cej5MJ;jIY#AF@Fh|t3xTc{LMK;rMxfGP0LvOsp0A+Z(k+B@FvYZ(Z0t(H^%GZ&(#$f{W1OeW8oc4R3&WM)NbxAH_L{Ayzyn2=*$^)kBou~E6n8GZcm_sxQwx={ERM^qF%a3t9i#=spr{#OgV?&&awotoeZsXRmdtNsdtJiI%A;zr?Heq=Lkb57rX!N&ahAXoP!Vf725%jm(sbq)A9A~=e8+By5hlifj7;afA!y%cN^x=tyS)+3}cInQG7p*r4N96=10*c3{7Cra2h8%&#>C2g5iS<s<icmkGA<mr4Z&5QS>n=(=Pw$2}BQr;uX2|<1Zz%XP%L7RyPf+9N@W&R4UXDd~*vCWMx8?}!e=CGtEi;?bM6ubhe>i3mrGn-jq6iMf!#wWq>z_W|{du>*YF<+L%Q%&;1q|P9-<S8z=JBpvkX?C&A%Y_Q5=}5zSvH2iJsy2t2|pLCL$I#}?HF%&cu^%GvvW$dCvYwwxtl|)r@%x?il^tV<;L<blf#1~riGpdIle+P5$v?k%`C|o1C6l23Z<>Y$7ma_4(1&gq-=Kqg|qSj$uMe3ZUrud2&2?pf|w}lfzGAP%)C9vIn2QwV9dZgCO%}7yBnOcE{!AGpiTu(;ucDK;4q+VQ2LP*jG#BG<uP1ok~E$%V$hhdFSR0aioru%h(KYkN6j!4zbsx5a@#C_UHM={=6ZYD-;6W0Qh4CG5TWmRFKhQX`JJW*HHAwKERe_}C+u4<s;N8Zah$F&XsG?{LJ6t^026<(p((qyR<2)5)+BT4%T>(17d^(S6MA%A;};It60aq26#`F(NDj3{j|pjQS;Zj)qSf%mJRO8IyHJT;VJ+Sgx1ilN+~|^xiM6;zr&;+2kDpc^S>oGxh6pf?8h{Fo1x1k?$*s*~JDa{V!$*<q3E0PEB_-Wz0K6CWSw#wF3~Uesy8&G(7cO&QB`cNLt1RM;K-8H*-(|w%MtrEzex-0#&ZJK^Od3y?dY)-OFE>DmH@-%*@+8l0j$F$y0#j~k-!8XF-a@P1=wLO5`@i7^eaq-U+J}y*Io~eiPKYry_sVkAMB1JVL0Hjuxs}Wa%*3Uxwr%pnN!JTlW0O!u!8&OZjP$(8HUcQ%yRwB4ME=l2I!agLS24J%nuF9_N2kPVGzu$CnJdAqevUKNMH1t-QzV5+p<LYR+QJMm;G3<!or6qPw#HB-n5?!6Ag|B27H@_f0u2P)ENt!U!of$#!NQgW$UZrK1;hBbt=DC&qh2iHYHLt>DMrFqFzc=w;y^uH8Mp<R7dCldUN~BjZ8}LBLE?04A(nd}&<$%U+RN+Yzq7p~*(kh~G)LBtK$XGlxKD9O%9+q#c8&qBKpPa4LQA@snaay;CUcHrtclb^I39qyEq8U*n6y=biO5!iU~;wOV$1_svt3lBgP~PoC&t0SuG}h+`6@{7089+E7%m2d{s&7=uH&PjH~|9qv=?<kL(i)-6OF&isn`$0#qe-ElCx>m-xr~iPU+Y4MK<MugEBf6b2=jPspuDR$zaR%o}7qrWcgEy`V{y_OXf1DdTYU9ED|c`f)7V3qfR8VESeKQyyuqo=&+}HeQ0IbsY2uovIx782vO4o#wiGtMH~wf2K>m%6@I<VphO|E=O&+q<nks82Jo*KKU<}{tQ({zOUh9xjYA3l64sDhD=}7pspiF=f87NkS!|5lR#!d>)=6Dd-aAiNj&UgdZmV-roF^i{H|sYIocnSM_zFq1JUj7~IxtY=qygqW(}c%z8;P#K%z$Tt(O(OIS$zg3x~()Av!$gP6EwV?v}32K4UtBYbW>54gD6?UTrKRzOAEzmWi)AP^d(`OP5rK`k%U6L$rufe-(l6utRdGb3x3ojBq~HO>3|6a-%KLv^g$4dw(*>2?B=qHkWPT<^n`6(fQKdfPX*urBqs<}7Fg79POh7!T@S~$o;;H$;4rW|ZamDEsY%5NNDFn_qE7m!M4fbX%%D0<Mpwk8^huiNGZeBgWLcv5=~Me#Pfyc$D<~|WS)m%8ie#pNQd|j=S4BqNNLMI#81=?ELnMLNl&FY^1~3W0lCh9OYDgqrVw=?hiQyE^T_qU}B=YjMy7<mgN)LnD6q1KXO>$ggUhEJ36`^5@nom-Nk2z4>|Dj^I3HlzGP|eR{@*a|8d=kBp_-9gFSrhimx_#iVRp+=IP?fEj_ECvFs6_24Ju9A-4z)Hpslr{X+A>%=^h0;clR>VdA^s^UEd~ah41T2mMPznto&>AYMInBwGN$s`qUJ7|X&o<V*4Gsn;Ibfl%)Xg+Mh`6D)zmCYt69YW1`8Y62JtF!X&a@b-%JJo)?)!=h<X5-A~G<0D3o+#>;W^^!^4Ey%Q`7DkwFm%Xtr!xVP;_hX>$lVIq|*3R+A(RNkemu<}+HEK_o-WTMC&kjnte7m(jHPz~!GTa#m(_kOEERI+k)91QxrW)+4PB>d$i{cJHH(QedKZkBCtyB2Fylf`Uu+TosD_8}uz8gGC3ORQB@H^jM=nReC<fY6U$nHI7!aS_=pbn@4iU<!Y|k)28A%#)uI;Wj=w}B^`cCae+)#11))txRaW{$D~)aBZg>S@mw}ZBep)SwqHrn9I;jnt-U57Dj7IlId7vCDAeJw$CH5cd_N0&rJji*N*U7~Rjo8_3;#4jj7juhRm&**9w33x)47=n5eWQH!)LI3FCoy6Zy3`F_FQ!t>@brl5=EuTDHAj2I%-4s^ViSQZ}XDH5t1Y8H;px9!l?P-4_(wchv(lilRPE5aV-kn<)q2}d8$yIG-F@^4T^~jr^qQtD7l=fx@LNRYyKNiUeUNIhD%1rox43LUy!CiXp*LhlN@y<a&;*UIJ4kt7pscgHB!noF$HcJrxBm@N{|Q&-aufL5;sa0znax+@S@seHTYn+MuH!nM#D4Lo{ub<y0Swg@e7?d)7jBkmdY8+KZNhInw%P~#z)byBuk2?Q`#l-Og1DWy%U!ct;Ro<&w&bFDj=O;M(Y|sBCA;Au``Do;~VpBf=G=j<M|Q;VISm02D@fSTLNRUM9BvyXlU27>zV6SMd!3mK4m*zUv@02oi4_~=-Sl1Vd89IEQm!SQXyBu^)3nhl9#T@V=4ffxZfEWuT1m+3tW$fOHOJ+&X8rH5*{qq*bwt8W%)m))nMg|#UZr1;QnCWY;ztey1u2Ncf@zIge0#86G@l*;6?>Sxd@XbUNo0h%uS_FNb0C+K@L%dPl+B1us(0H1`nV<S_-9|G8mYWrGY8%IBr%Y5%{$n<ibr?KQ$atc(t8Rl8`{y+)A>)DsI>^lR~9o%1#%LFfn3YeO1qCT_l+a8W&3}w?yk|wf1msZBJI3g{ljb5)4ILzGZ2)D>&BQ@a#0rhA381%>Fw>x2SgG3;XYCa#$;bT1fIgq&80wI_{qOpCP~5<NzbYYn4RL5(4_B@xKb^Lv}+AErB#$U<3v+IpUXo^&`>8Fb=r(Xtmi!zPwtERt(o?Xcpj*CcJ@K+(;l%vY`r++JX89@}0TQpXJ36J#JJcF;+vVSV`ex2Qvi_0g8n<c_PL7&W8F}`frImu~cj)Ko5f`c(rgIgrY6$GcZRZ5s)`xZo%nxWDtxO(q>e83ZR@e$gRz=5PegyC*o17G>tnfDy}nEtY9Y%KF~3u`2v3YM}#!2;Z*7L$bVU=z8;}Hw0r_Xoj@d|9FPdt3Nk+okJ>>30&sAxD{l6|-1@o0L*I8<xXFO)as8chJ-T$m@`_<CG8U)&7F3Un^qERuitQB7L*A@yyaA=J!N5#LKaRP~9pDJqv-X7fZtiwry@qb%DNSNm@(CsA5-5Z)BC4g3uAKx}>JprW?S*K)4xOZmHL|J&glM4iwWwBln%tpOLu5x(1PO4_nwDCafF5%jiFN6uxu!~4G|U_1VZpOTt4G<$gVU>>ia~Uqev@Mnm&c$~UAKbvaZa)xXkKg$R<=r2P>G&ieKAT<W7v+K5eAofjo{7QU405xj+7RtIKY4fn=~Sh|BW;Lt#Zgw(4PVjwtH7}4J#~51gP?FHPly%dB^VAQiOe&@e;3hz6YcM$wL8U(;b}$S}2P0+Y-bHfkxXZ_K14Me#ItdF!5&X*XJNH2!GEkbS&N*C0qLC)eD6$R28^TXqD%Z<|Ioi1F8jDm6f9-N~%A+d=>YkUCLmH`pjy2h$q!At9a1tyJbhbGWx?bP2L9dQv)3$BY-OgB%@Sns!twQiMqw$x<+S5B*!$D3he_2DTzJ+@d~5PYUxV<*1mQ!dO$%1pnHxsMuz3mS$5&7tri1L&BswxNmXAhJ3lYQc1hLwi&PN@Bh$=Dos;*eI2PC2L|q7Ut<Y#aPk+z&yk3S-*@aO1;v^ljWKBdsfFHJ=&9@m`Rg|El5Gs#p^m7{7#$mOlrN7yR0Pc$tkEh;{CM_sdZcR?el~E=MA@q<=pchpk36Oml*#sN~VK7lYPs}&4xd<z9cR)*2L->il?7(-@w116dc8Pto+BJIKO3b3^cP#CcK_WcQC(oO>c7So9O;q;h<EMXS5~(p{WA!E{t%-dcrkBeAEUFo6ck3#jZlxMEJgQ>Jw)#oa*ZKZwt+lc9hKeDb*X2gbSM<T^3V!->rw@>>>usJJrS>~1wo`rYY*s<%Zr*XX&Lv1F9`p(tI}vOU@wQRI9;!%kIZe$GOc!-J<-sX>x`(31kr3t)njX~7$dq_!tUW+VUAC$0<o~YTJ(t^F*;kqs4v7S|?{S@ybk!X}BL1Q#0Ew})kyu(wWfVhzhi@UmSL!O@$RvjtPfGhLH7N^YVNs|`%N%3>sUkbeOf|{~g#}(VHxg_3wx+sL20~BQ)OkY{9>V>>!6-!*L)YW-&oZS8l&ztt$nZ`j!sSevC{ZvyE-VWs!p~R{O1XM^ZfXe*Y~;zqzi{NNj#==OK^CV1Dl{?=X<IlhE;A=Y@g;0e_khLJSON0|<Q+p~_&N$L#o{(pE!r!>O84`0({>r3WBg#<u*5m9{#cv1%XzX?wR+5w=tvs4Z3+D_rY4E)(5^XE1Sb_3nuvUMRRlIx-)rXK>i}MIrPsQqz;qNdFU!r!H`FpdnqaP22c=cYI91T*6`-$RQR$Mv)pgj_X_Qx<nX^}cV>-;5f=jridl^V9gUIdaQy$P2x%m|!O!5)+PFyy@S{yN~QsW7J)CU=|fGvQhR5RH`ePLBUf@3R-#`?fw5db<duC&O^SWn?;!X<iQSgW3L>i2^nKUmjEUpF*B5}65IdqQ(`H7Hehgnt7v083Ful96-;Pw8=i1ICRv;Fi9*pUqjW5w2Sv54V<dCzY|)E;6M60nM0`70p|8%&*ee04ECvzzBf?SQRU`U<XZ6HP0bh;z27i=a(i}5Y~R6v>Zy&@v5+g)|U)C9t25HcP;yyAco3*rlhlS%HSp6Mc_=<&bLZi>&k_dgIHT!Z5Y%|0X5Z7sZ|9gOCvmBX?@SA)CO4|RQ-yU7!#VEaMuQCP7!Rzjl|!I;777lDr1U4TTReI6qpiC*<=ph*DhdXf`+*SM=g0y7v*kaTlKKD*}R3cBX;7m_1T5o1rqy+HgiHK-Qg<=JvwgyWpzD!BEJ^OQ?qj~6*N+Uc!Zc&A+QhdsB6hE>Nks^cEq)lBxs1|>#}Ba8>Xgm?&JwV|BrL7<jddpNm8C}MnaBa&h^aIHXehpp(=t`#RAmB0W4_PkVCkLS)`@C0YVcXE*DBy;LE8#Yra}jdCbqVxLss<;{S?4Cp$|YOyZ4`^sU11GNQzeo>X^MDPTJy$H6TLR&toVn<NV9mIoDcBCBg1A(Ua+^1fy1ZhF*lizZl$*+t2(MPAx!8)6i-BELB6^*mdpf=8G%opVjY42{E0;4c)v?O0JV6kNuRv{o0hK3)p#H=j|eL94WfCEQw*7Bt+3uIOD!6szh#&#vE-COZ{ytDD8IO(M%fLu&Dx&AKa_%uv|R=}&R^Wr|eDY-S*x038bJlKx2f`D<F_=X97l2bh@K6OnE3w*Uc*CD8j+nTtFdmkTuwjgZoag8a~OS=31iJ=EO@7OD#ZQaWLknBzBJT13aqs-GHo3Zi2Pp@)8_$U>q}7rRR}he=&VRv~h*g6n>uk@sH5TE=T2A@3N}PJ|~E(?G0Y=!{{&4%1p%by61_9z9}WALSPqVC99A<pLr8fHoy1EhqesD|hv9Y7yvA4T+-(J$p|ph2O7)9ln1-#Z(|ZZO!E?c~f8az{CAhx+WWjjC0;E!PdC2P%L3Cn^<k|-LB8OF*QY`SSW2MxK22q0k&D?Kqa->8YKEO%qgC1dhNCqnQQ?qOaHRm%WMc@K&yTnWi`S8RI|vB02gKq<5_f9L@6<>hO;*SrRec8KO{+|v1<c3Jz>V3fNtM;5y%oioD^S+NYoo4S^hOd$-??i2JjS?xnl$&F`la7ZeH#wC(K!*U{pq?5}Ht!(`GUboiKsn2v}5qJGRUhE%U8qFn~~<HPTn*JTDjYG6w`I$_#PBMw6<UcgJT?pxUy;ztD?ns)Q^r86uwRi#GgG%TH7ewKf>FYQ~D@P6E%2FymCoh86%})wanMowifb<0@PMMD(3jRL}4qS9}HR@`5fhT5kc-Cn%uJ(h$_iy|LzY-X@5~xdPEz4(m3xxu%_Z7NjE3Z1dW-HP7Z+=`u30mnqFSy4B9Z6lp=xWh%-Z^I6y-Q+ACCWU32t(cO$H?M4w1XRDFG@O>tV#cANnF}*BgIM8%oo02%QW=|-TVrGT&Av&yZED_&+OV)UM`fhZYuj(@0tQ*$rtnFr`t_?|$l>~gM%bu!UrloG`YW*qihv&c0pb-yEF><a?Mz}F=&}=5ZUXMJe!YZkEv`)E>;LfK;aBDkM$2P08IeSZ7NDv}?6B2to0KYcS=xPre@i7wu6yYVK62p9(t^FD~Lut%22z&}Fu*yZ>CQ8E^S%5OTQm%Td2{PChT)8NtzD4t@uaGvls}av-mmB4V3Ca9%;fKzbnl23xQMQ3|rPsOOt9^3VmL<k=J&Bk#LN(B=5^MGrC0+x;7Gs4>8^7>ynw67{$S-uE2rZhQ*5!CzK&Ll3V1U<iF9{<w-B&zzy*kf*yhc{8mQ!CSyQliqYkPxYO%Ixkr$;@F@)I7YllA@>dtIAA319C6>Fi=1soT<9$6~d|@az(})xDutk(Z3CG1Lp_R@36mD>94@_|((V5DFX)LpwDmE#cj&i;PLnQo^+oQ*nZPGB#`22!5qetqi)l{Z{6EnXblK&Jqisf}N<&Wd>_rY8y0Mr30^_OrG<~en_DPL7Ll{-dP6>HN%YI1*_6EZ5FRic0D=i6~Dd%RC@6Sq0(38yEYWzb)@gpkf<TbWysYW?krSv_i93hYg`S@p~^K^;Y}=<?y3EeShX!7-@;JsB>s3VDSEKhuX@F6sX-Soek_i$US+ov?R29R*(CKNnky76+aME90ykB{rZ%1Cs*G{J1Y5L4QzGQ{sJ*%BO*R7s5+ox%VuRCNo2bzur9LIj(qx>^sC!gpeoc*-D8x!y8_*$tr{tPqbh8BqV-y|vQt?@F^T|RfffuP13}CKln*`#j4G1!sqgtVssIFfMvVB>SSI%*i#!?u$bR)`=h9N_F6dFS=Y(WRf!(2&`^R`|~l9XC=1@c?~|FZ6RALLReWJ$`o`zRo-i!0i;KDOzxWHn%jun-v1#{&=q@bkH%^B#z<BHqcw@a6ND(b{^*JgD;uKr>e9Qfz*)r)L*f<Z>c5$zm$F^Q3<0r5xVceYIB@`F~K$rV{{iOd=RHaZ&veEKT^kYGf(J9bHzZi=3RL+XVxeFslL^b7}ODSzGY^5ydbnqak39GKJD${<E}KCCjrZEx%S)%d_^K>Obg;5>p_p9!PAxa_z)|r$CF-A`lI?XF3SKVTztI#u``mwOM?<k`Tdx8%_<geiCH8UGuM+OmPwuU@jvo=`Bk31r+s#tA&>+rDEmhv&gezf5y`#RLAzN4zM(VlPOhOmCeqs9utJe%LA?in)gLq<Z8%0!#ThM;zX42<e==HI?-_IfKC|$c1tpBTuHQ^T=S^bXz?MG<n!W?T^5^2pu!EWN=q`Q{P<6M@AT!I>7uJNZaZ9CY6<yT;d!O}?aMLKc?VtOF_euYNlx}vC-U(kk57{zDNi&$oyXd&Dry$F`83w3R)1w3repfO2vh!=N-ssBS#7e2hG$CgoO1tdYa@`&-w2|JXf<}3zFsNXvz1;z`j4cgSq9*$49xkPVIc-80_z&w7@BDWY2d81sJvW9E?z(<jP>|Jju($ni)STF6K7x)Y?i}i0%xWP_ep``Bn1+t81Up$;aFT|@<d5ACeC=x@OrEs5R^#^d74%q@tmq8naeh?qF73LF>Jlkoi7`ZA<U4hB3g?n%O2^H(qCRU*#gh;$s5k7)LR22mx`7u1SUm2t+my*#G+r-X`?}{f}h6rfiId!hBvswMV4oqdRZA^2a`Y+4Y8N3MMJdZ;42hOErBbfUD8$+ST})6L43s2a|Q{Q<O(ZaOzo|laXuHkZk2jB?88A%fhXG#L4vUV4LQjYWGv-BDjPs3R+cz0y()>B!XIV%qDVI)-I+ydKkgS9xYv|RxO~v*1A9ygjlu*4psSp`61UnoB8RGEmvUOL{JU!W4xjkrNk9uRJu%B($W;~DoY(RI0O&LC4Re+A@CGX{*Y2j}BsG~?YBuvn6=X$AnbqrywrjJ&fn7A~C1+bsC|S*<Fo0%B*1gvQmgdxyQAlg%vgn{LBWWGeh+q@QRDf1eP3YJ&4G>B_odS$0v?z4}7q-e+mDZq=q_v*-1xiHbH4?iwS5eYn5Vzv>h*GO(BUZu)REE&tO4y6yU&O4Yf84sakB?e?h;dV`=E;*fFh}<-qfI>g(Nu_)s0UODt7zWQLo5Dt_#p5aOQ7K8pV8E^(Mo)1Y!)nV`UcvC4~n<YvMz0SZ`FIN-e9Z7aWVGKm!-#A<7<@FudbW?*g)<)P%Cv(pA6RTMvmpzYmj*cO(>=m41{HF!ZCM67^@*-@?yZmW5y8`LZreCu@@Z6LPcyWW{?SW$%%Owfw<OW6U#J{fN#t;c{As$fwnMtUI!JAhL$dQ#jj+6hK~>TpX*jLg-U4@yC{NUC^d*CnWz?H4a@)*7p}mhpU(g=;2#u2QHf#|_i@-;gk6BQglhBNy~3(IF_e^&M-8C`PCotyeMS4aS7#+rqRIM7&(B<EcL!D=p|L;J2IPkQSG5n~IaZpY`;+Y=Ho`%>4*RV<i8qx)keSV>soTGA{||QnE?W')).decode('utf-8'))
_ACTIONS_6C12S_4Q_SECOND_YARN = json.loads(zlib.decompress(base64.b85decode('c-rk<U2j`ia{MoP)`Lk=5|uZN&D}9pGcsg*h0Q=143G^11e=FR-h%x1IFd+S-cwy&)#p(5IC{ILDc<vax~r?JfBEl|fBo(EfBgOTlYjc<<cH7iZ{Gd-;ripJ&v%=XhtrdP`|Use<v+jt&zHx4{Pz35|NXzdJpXd?<NL?|)gFHM{I_4Pe}4bd_07rY$=loelhbAM@y8!Gn-7!!__*1;`||PqkDKdHC#RRQkAK?S-2QxWy4ZdF!`<z>&u>5N|Kj4|;eSr29sBV9?O#5B*uQBp>Dw<S_nVKO9^3l!?cJvzAD?y~%^nU1;^XG#X8+c+`CGR?H+dCk$n>@Qr}<Q%2FzX;&K~UHt|gCivN-7L^S8*mKHOZt-9+Pw`m_B5@U~gI$y=ZQWICQrJ03s#dA}GA`uaRm!Pn9e-dxY$zh55LpEh^%MKu5HaP`2YyPPkgkGG%ai>O_kfBL_jaq!8kcWf%#!8sh@*(mM%_xAdEX>Pytv@<7Nx8`y`T<uG@qcHteI$dD@p~(R|p;^J?Eze^Q#%wYi&5X6*(P!*=-09FA{O)|`?T4_PreIwzgu@MNhVW?RXUjnsw2?)JPCj|tmg-|Ef0EB57{cch2Fy`5Z~7qa-m!c5a`t{i58lA-$Gzu=pT9{beeCbk2_Mpd?cYw`H1v1Vhp+Invs>jXuqKnk)VM&#{ObH{b++$|w_t9Mkgqmo#F!Smy}h~Fy#4g+pEh@&-rv0c=fg8$(BPF{Vl0vJJB~C5+gp3mo^TKC9Ff_VgRA`f!LR_o>Gf~S@4Szzx_6t}f1Nf7Fz*`kabkpng<J76fH4C11n$-I(zeWG-iK*#vp%K+2poIEAZ4x!e9C^1jRks2e~@_uqW#$6kH$?dI#BVTO17`Efv9hu&p+{W`dnWHcuIc`ddr6M0F3+nPqxNjzWH0=gxHpO`>dZ!O;v)My|7{Z`fKBVO}_Vm4Yg81?z&+R+Y0UBd<dg2X0Z5|Q}6B;AvMx*$gW!HkgV7bySGjbEdTBl+uqYTYX}jt-gPI?`?bs1pcidrShyV%LXnQsl(pY5o2cbMOooCzMi>1a^-Hl)f?g$qkwb>g!8?btz8~P~^=Dsy_7C{8I)F98)QKbSFod5%PUkj&5`^U2cQ+m^bLTXCrRX&pcuHRYGP8&(Ac%)bIqfG=^<GDoUGTx!{CIu$*QjITZhQkR5Tn>=sCIoR4$*WhdMF0%;IuKw9hsmDNa2IN>)6v<y+KDt)oxIxBbCD;0AD#+cKbED9h7~<Qy%pFFQThv`o4*Qu46EBjt0HYz#A$N=JtnMn$)Y=@cOg8AkledIX!=G{kYv*W9l3e9~X{k^=!m^{B(DH|HJ0)?r*@7DIrX0hr+i*8s>61+{79fG-B~^1T^XeK`86)G|b336ji-TV`QNUJRQr#np!7QtjR-|IH=OKK6VegD?R@?4QJcl$dgTr$*%)Lon79^d<2TCAnLdE@l!La79o0iYG@_I+TL=6@FsAzou8|~gh!*}y#}_vR+#L<!H&*5?V7WP!tp7@%Mu%b7%J#^Rh((+t7l+L<yv8A#pDvazrDSAOpAf0)$@NoPtce1@!d(;*4z8@xVOf~($T4zgN!0Eh_f;u>gZOG4c^09vDfl$B1BLQ#*!}u_7BKZ8f_?)ril3=T6|2suO%3&iyo%?E`98%Hu{+&WfFSZJeBdzO_U$uH4(t3^Kh)!M1(R<I8%p-1>L*A=zKff=;)iD7L{$lh8aESg91*S7C@e-&eRxRz$clRx5u)gF3fD%MJZwj%&!HG*{yP`3}&<1rkY5n(wty9^flvLcwh<2>;;*qK^wr;%&s~e$xwXlY=DA~+gm>PB8MB)vxH4H%;wEgw>|4Yy3=X4UQ7d1;06Ys?V?Tw5(wu1I?1+Xr1D*0iex({xu-pr1=~S1`Bcv}XZfx63WR^qX&lc6G9`e4G1G5g;$O6ZVK5bO8;f9M7%s*=W%f<Q*Z|f+6QXUh;jIyGJ0Ds)r{e#W$d>FK?L%qA+r>@BlDwQH3Io))JD(=ELEHbc&O0`&v}^27ijGnX@&ed5fZW;t*U~&dItsvz+ZOiamdNShUmo7Q|Fem~0{dD|9IwH?fFq*$Dg8{r#T)E)G+^-7hWP3I&0h{(D(G+_D*=9ug~NC6I<o6^mP1Lq>lImbx+Umx^a3Xgl8S&a7&#Zst*tOTIUZGqCv<4O;%Vx?o}SBW3xM?zyf0fUt+jgK)|1Q#Wh)5;jq3(K23kYN;gFqMMRQ7aQ7PeCT|AmsSpvW{Mn~(|?+top^I!sDA2Qjx62RalVJ@x$7CS{|TH7^=a{zCMIYF5AY1&D|RcHqiwVt@nFizG(4pq?S(<D~Y=ni;u3Yeu}Y64@H3@zFQU^8`F!6;_I_2)nnrz@|e8CUFN&{auls+H?&K575Fl2)+StBc<qGL^IQkhKiixr++xhrKr^TOa(Alsh9dayRQ<LnM!;kPZpvc!(1<K7(?|!)s&y@Qvw?86GmE&#Ag@S<HZG+3uwkum~Xeo+e{8P=cYg&vb8^aCp5CXHM}R;!%^}pG694e4#T57QnWKnps(tg&Lg12>|ikDnS7i<T+Qcne=buHwm!96V+^mS0J*mD<BAe;{1~XO5DoG=WTkJxMPVj292*3T5hEYIQSUNh-k?golZJ;#QEqF|B?%1s7KR%3|E2$5NGHH(e#Kh*GHuy5iu5vWD!`}vp(1+p=L~CHDcUc^SE?g7V%a2szbDn*w#a9xzIL{^t*inakeC_7N*)#$I+R?NBps|b~I^LZPbRe3YpEv85-WK`oVK-*GSSfxweJ*zV3?qimd_`>$lLX*M&7;cj{QdG5!4RAp0@g`AT$L3_|PCapK4y!0o;(uX*sYmAo#cumr&ai$`4Xbt?=qJuI%f=TVmgp++ykp9R7t=MRS!%Nhh!gE4!Tgh$1`cx~1}+%ucJR2hmUg?7#~9j@t1#ISp(fHZdzNrDHCYy(gNW!nMxcd;<;0Q}0f-SB%zjg!~!0?oZNZUl|mAaP8=7R*QX@<HdHveBe|Gf4rAQmS!l*C^7VcL2Q|?_$QeC9qYg2Ny9ra`9l$0MJqbP1W!&35v~orb94Pxh~l#J7(OpCS)xA=Jn;^N0a`6oZU%vJkmzcJN^gc+DGKb!@ew6fn?Ppt{1a7H?qys)~UH#G-Vif;mw1dLBz>K6jFtJEihqZ$)T0SyV4=@$tIvmy6w^YLc<&t<4kQzT@R6mi9#CCG|wWO<Y**SodL8g1SMOq)Eq0}(SuuLlp&YkfHp@$$X_<%B_r7R%d;vv!XcAy1u2PY3|mg|(J2sn^qyv$gB|NR{Q31%<XQtKPry$kKR?UCo{m&SUa0k_s~}2|%MpCs+Dg-&>Pf!JvQtx47}+-MhK$@@S!pd4USQb;)KoB(^}NuSyxgeIN$A58)5BBdY1RvKsc1u}lU<|hGJUR=;KNcTD9IgYX$)B+0Cz;PER=L|<OL#417nd<r-LmVPUz@dIH1LBrN<n8O??v%_U1T?s@=o;el!*BXRnfr?SySdd#k#v2sbN93{jew)<23|^C04MD)mXB!{qCo6XALnRCNbos7FgO3X4T`EHdMiO7{b6G0!xMv0{773D=L~p@L#v0$dEg=<L<X@~7+$I_n0uOHNl)YQ6e1;}->D)h6)3OL)r5t|Jc+>U^-)hz$bm0Ut>#ZvYT966<kMq2t3o0RMsF!9*8tIs@x&HP+qHtS7tFX(tTf%^MHXTiOG<%?wFlktCR_$s*ggV!J5zlQ9&h2}2JxA3JNMKJE+z<(NZ-U8RIasDamt3MLq+8oNDzs8Ho=X-<gfkABDz8esAaEKy5U6)@xqNzMkqS~$=ki*UAa@|uVrPvKEAwg^{6Nb=N~93muzM!Fq7N)V`oRHVe9JeOx2T@Vb?1ny8TOJ|&z<BPe1_*1?^=19j-OpXaqBo2F2s1J)7iTmT+KuJU)5H36eI<DR*YV4XV6TYE!<wH#alb3KymJve}x%Zl_`k1@sua~%J5?Y=bK?C5=vO}&=C&jW{!eJ$Mi5<g1qsxn(!uKXPQylQq-g3zrO-lc^zeon-3X8>*>i3wm4akj`Url0T1mN&uL=$FzbLatN3_CIhKF6f>8TwTyTA!`KPlz|yD@_j*k1|CLN_8-EMm#90zgm<s6BY2H6VqZe5=pX!?S*Q}PP<A}xeIEZ6bc*B{5=MV=p-A?z3C(er74E$xVD#Mu_T(sf^OF<8(?;U`}W7`VUUBZineT#jTzB8EA5I61><s2v^0}s&p5%u%1@_BvK+*qCZ|!`j5P{XcVK7_vW-*et_q|m0xRlfFAbdLFH887%AwkfsT(2Q9(2`>8Zt2uu6W^6)<UgVlh`EMHnDJZk!Zw<+#ydKwM&8&i~)6pa@EfQn5jjRDePV2Aozq75m(TQg1mrQrqP(1zkk)Z^$`NF`rbGL1-C3f=CkbmPEW}RD#G;8v89DuJKEI9=<ZJ;;wbwiy1IoP4KK`jF;ypyNA`QfZl&F<I0+1q^!deMeUImVW+@*-y&GLL*H+r7)dobBLaY>?+K!{<>*3VY>SHTX6529N<RZFcAymQF$`ph5?x|PV0QU*Yh;E7?jZ)KE1;l>QORsoIGT|zLkqv&JG~~eHk-YC>d29}LvP7I5T-2Nu7_MhNe&xk9X@sT};N7QUXo~-%RjW}#(F16cN=ixMif@kN-$dTbIre+Lb^iw0QQt&_5@C;G5U(Qxo<%3sq-3yvsKMs4q16zi@|*|`j*z}rIMF(&tc%PE40fIrUerjF)>7JG-Cq*NPA944iSSI998mAtxX|Q)q_&kLEvKjzwP&+_SJR_F=fSfObl=Qb6(6<gj&xSit>=q@T^O?bZ4!v3@xc@^Thl^cWr85#{%6~45bABH4v4LyxHxmjx^n7@T8M%cR!|X?rIS%lb7tL<XDLO6c9S)4<!gC$<cVHm-iLE%(NEim+)B~m=E)-^`N2Xym(E(_+1U~=xlg@w>D&*{{S64z8!xH5a6EzDtla9r34$S!XKB=O&@^2LbYLDX!W)cIpN44hqTZ~9MaM2)hK68u((vnyfZsP|YXMgg0Umz5X$z61&>4M#WOYTLPoq$Xn@IpANA^$2S{jzl-&9{hq@cb|jzPN)etRm|xQ=N3tH#$l{Ae->Wt<63%{N2eFDU&1zkt&LSTb)X%@!y$)g=PB&*(7&0kBXB-BMz{3&kO8P>t56Ev3+c1-OwsZ7qa5?`N@QT>(K2d8(a=WBZW6qKU~+QC4Uk_?;f*%+}J-(^biB`55N&DUY)Ko<g16>o|;^>Es_KpJ_C1rfPkW=36uKd-o#_^j8#q)gd)!leU&J0V#AL;loMJt}a`NMzdY{p%x{s3&LMp*8v`{JcLb)19b}|QpX1!8?;tI=;_(*VqT{_UP(@W8flIvPfN4jy*4<(`U<|R9x7Wi)09ZQNS1y~78Z!zQtcL&%|Q|kY-NL|z>^}}-@8JR6s>4_#`OU0e?`_5@>yi2kJaYosB#Gr1>`F5b7z&wUs)l96#~t17QFi!oDjwa6`W<5rG8eW^LaVy_c9{{+%D{%>?F^l(5PjuM*Ts^T7Rzls8n^}e#?HuGrG1Ek$rfgO@BiP%hM7FYOPhH{G*fW-IaIBY6@_OAahM<&B0DA0XU8AaLa;`eQ5)50j-TP3BZdK3bCbBgnEU#wPRc|?nqK`Akk{}2~SrJsiR%yVR^iZd9NgAyR2E2m|KgBl2#jI+^F(~sy=_Hdn8t()RgT@#geI?5ZmEnLiQ{Lfo>_`@;_XYne<zs_Mt)?A^9a-dW@aQjJv}sB-ZL8*6Kx2%!lGY3SnVLVaky#uM{13aSo6ROVAieVK1XyiDWAo^f(hCg9KoeN+j`m>{LR8<+B<azglZWCG7dRN`t$o@+D}<mcVNSaN8Yak6eT^S3s2sUzp{ITWN!U8V`0W4+dzOPiFDck!yK1tjeguC7FO^FkAXn^^u`xNs=h79CT#J%tLLeQgc8PqLG3uay=NTRuoqtS`>A(O<_OOilUB@h?G3|BV}Symrsu|ODFnRPf(-P7#fMbx+6=B9^)1&Nm%Wk3!<ae8rL$2>phb)vUHtWt<oT1ry0|wC#ST*n@s)Inwv1%B2JB{Ipn2l0n;`Tg^_{S(lpJD)RkbQl6?k_O4WX)>5-f;fjbvxq%N$KmUew&PhMp0jGeEgFkgfo0B$sx%0u(&1%C;w=sqVyxbuK7CD;98E|gpwal}<{)y()=xf%fB@k)g#+4T>}=(_{$_;VdgfHakYwHzO|ln;+;_RV+i|J-foT-7s9#FFLgxZ<Z;+jk=)>XJ>c2qwfwn=++}PRzcu+sR~Q-+ICTR~=+2jpilPAubn^c^sWmzt6;!v38U5l-~^xb13<Nxp;1u6}c39&a2W;FmTM%5za3q@7_%jrVCW~sJMK45zZ-^`4s;+fHRk2knOCo4ouakE(`fPLqBcq;Ovv*^98M(G*Pt3Q#~uP1u>~5v%N)*;dttxhi`)8_Zwsg77Ov-Z(K*Iq8CbYfnxF&3&rEG^)QL)DhH5tVk4R8v2hJtMpMj~U>@>9QtN{DPs+kz2cjg&jj)W2oIwr3*Fm-P)u`U{0l9a@a@(|eHnb~Eu(ja1XX%?PM>-WO(Q49Y>OYapio$C$0tixozM#8gi21N;UZ?>{*f`_R34`t|D0VWVA;pV`0b5-DMit%5aa$NiCLkUKbi~``ShGTpHx@Jyojd7CC~sbz6$(V)4Imie^{H9*;pFLEM{=#z!>TUJqwF1~37yrRODaVL8A4OlW;fK`R=SxNu<c}fo7QFw50Z$1G>`pIr^N-N`_e5d6~0I@R+r_lO-IE~z85EE<4#&i#QDx-m~S-}9lHqN<3C~{s6(l&<*|^v*3AP(+Pu+c;fIAk2}RlZATt-sW0K62+LhO8Ai-82laY&hSZd{!nmGZoNEreun^dhBRV%~7&%4Z_)@9<wj&<s7aS3?Jx!L5fObGx(D#_|{p7aZIo&eLv#%7rLap|0qt;r-M&?cU+UhKL9{z?;Z^~wo)5Q4in<KRnT;xkHNBpDJ_sM=UHe8Sjv%@HHn&3wS~GF!k%bhpu35xj<yLps4&cSU(bJQ9Es3@FOCkYJcxPL5;cC62p7<z)I+sG^gI-ZRml&@wQNzBg9(Sd#hX0x?*0Pv^Rw)$+hHJc$aB6COo)(eY!gB9xXu!f2P^Z^l&pY$A;I>-o9?huaJ_<)eOS)uGlXPTH}>r%)X93ri4#SHsLS?Xndnv60ObR=R0{^pr%FRsc7mjHl1eRaj>`N2n<IS0==Z*tiNWMhTz--_FLUfDqDlmHc7r_yPE>uP?{0@AqQasH!A&Vr7(pnwP8V7kweCSyC?4UP?ACa+m7A3?^2PgUZc5FA0^)Rp;5-84xz)wiuInn$2)<S|oW|Pi?D#5qf5zm6m!h7Ej6!83$epb2EJBk<|&Trs5|zL0}bz3wTyUt+FXKT1>JyS;oT52haO)fr;Qjgsy}o0-kJ|FHYyk)O2teHVfsz)yfsNYZ>tDcxTaB9eA<D%?U+NM1+f#Jfx-E>BVD3tp;UF7WS@Dk2ENAyw!-Ei_#?eO2y(~2k~%gmoJ@NUN9RHDqSYIaNju?mwmbGGS!{IBAV=2rQYYd)H|6gOHV2>jlJ{u!i#n_LO@K)Wt0TskO@{k$k#P1E2FWBvkF&lbCO*SkO)h6>FLNSAv7Z7)o-qp3$M`=`L@g1b~1ap;=5KCs)*>dhYGT<c=6KC;*L=&!w8}xZ?DKfVz<xW6URnB4?N>VTfy-%vR<OI;5*moBX?cFex0}QJp2$YME%eC7VBs4wb^o#UNb4B78l|h&gC--8SsOQ=GPV3ds&m5tX!SSN7%<TQXgZnONeGdcOR3VON{U=cam2m^@ZM;ZEghc5l-8#W}dl5H>FEFS{U#v6N}etjvx+#>Nk1?wp|(=(~2h*f@$79Bb6j|Z;ebON3u#=f?OP*Mxjd-tMeL_$CL*U8KsH>zAA$_z4pa@27{8!kYy(^7xpo8;*uh3SEX`#h^(wtiV!O}aHHNPZM3V9vqpBSZmW6~;qp1MZ61JWs$W$zpOLS&1MsEWcel})hy-;fP>y`G^O2oSq7hm9QwjmsFHIRGml0FvO+E<Eb0t?%&`Jy>>OTaD5fiahDXsHrGBT@@D-}@iYsrRa|51hT$U!Z!T*PA<9s1i-aR~HFq+CU1JXSVB;~8qYf5G$%R8x}rxQ@<%j-^4tNc6OwP>nUq%}co8`r;zV0^sMqm>9;_z9PRcNaA*>?th!6`8<5*4Mw?UM4#`3z4>&f9+keCh000LrI76sOCA>3ovP}eRo;Ns>|L8Vn1a8ogL4)Qv{<0TL0y&AHMW#U?$GoCgRMI~eqH8ZR%d+`1*&qCsI}@;a2b+^0^c#0SUES2z^v&$?935^TG<;VHcb|#O4Co)Y+iloIsDstgrZk**~flt&8Ze7r4>-Kxjl?;uY;u$S9%wR;YuM2u8mb51n4h>G(Sq*b>YcKFNvVd7sfgd1xw_@2m+Eh1pOx{7wZIu^YM)EGGl!qfU~~-#5!CnCz;5cqnJS+vq+4flv<vX5y<mdl{89Eg9PTD;67hYqN=;@Vb60o+ckLUu%Qz^r34rnhG!RuW~@1$cEXTwohChuOQ(SYjN2@71!Fp-$o2Q@3oI?eWnB&nXgqK2(#vv@_<T#zfOTKk4&W2GsYLy;ss1u#zSqSFa!~~qgt^eR-S)Mk>WP<`a8a)j0)(&%*yjZP#km}D?5|FRUXPD)b#XVtNjoM0x<as~`Qfqnn3hi17)~jpW?uN3(`|&Mo!5djmlVxN@*EjFVChY9h3tazVg^h&$%`d~=CYJLpyvL|3?iayP&`F?v>?P7L06`Kr`VR1Fl~uUw8Makb?P-?%W>&dX-THod0W3YkasF%Yz~~l(;h`k8W&>%IDxtntJs_x*UPIu1&YIVD5PxUCC(~hj;zT8wpY4Pnr#=4JkFkAuJOjc&?F6aR@<7()S1O;6%EUBZBioEN%Mon9KMktE0tLT{)b%)sofMtSoo}>szWMMQCvGOk1#}+lDWJf52EGkYn3#(Vw9Y7u&nQb!kr$~URA5Ej}fShFMOeBY7p)s)T_3KD(R)|%&PBF=g^r}ewLuaQV-42s=Q+GMwe2wD6XzN*jarWQC(B7P)J<mxsHbQW*x}>k6qhFF&7FeP+_Q2@g!j8GWz~@(h@b{-V=Q}NGNg%?!b%x2Z_%|6ohoWWYmQ*nvm79wy{LQu!6jKfZu6+2DX%(IFDso$9wQ{iuD#WZB$i;wr8d3G^*a3zPSwKsz&_-o{}gRkE#}=Dvm3I`Xy2Pcxg^>Wbt^p8ZEpW#NLD1<sMBm!SY*$hEhcng@*@H@ieqet9U}9Dyu%6o0Phy@;B+6=_h+u*0(Gp$Cz|{o>B>Y$7jFlqnG6;sg@@ru$9UiqFC3RWcG0`P)wa6J7pO%$@)r^WbB>L+i{dvY_6HASVzQts9Xsx>L@XiiaGyhW$G1!tf@AiR5+lPZ&!<JStU_L`4a|J7?rawZGO$dsXl6hT$HL>%#nQ4kt9o8r3UmN>7ZhggS6+;^?2HW`WqE&_0>zskx$bjGG6=0kp4o}5KFfjiLE<$K7tsxl9(_pD#l<nO1KV#)nk|ueYCYVl!L#e&@H>kZTe>X`c;Ley!V#@=)^o<w9JHLg!P!xEl&1s4%9`)HOkw%tmY>y`uJZKSXPmiQ>9*(%R#)bq5Y8AMQ*b1g%M>`mT-R|4MV7IqcTgeK~@6=b>T_P?dAhgWW2080YjZ)s+4Z7a^0>5A&DthL5mJE>V_136hJC3r<WD@NaB@R4cqj%)CGb<%ZJ7s6l7A>h5@RWG3#MaZR-|D$lwrKJe^ki?5t|Zn4U@UCMyoqz{NA8*eWHev^v?ZXnciA?mTt4k~n)W5I8||fXUR_g;q37Nu|i@dud>&lSbi`4cR@2KuDzg$lZmy9Ihk#m{;M}Fc7Ab+eLz`CUeruhld`y(`IV@9;r}nlny{t7jg;1A=<vwuqBRemWiqA7(W6$BW8q<&(dNu>`0aM0wWOJ>D)e7vTwc7Vt&*-A3#1oT8ZLBRu_~*Ily0It+hXr99|QA{AP<8b2kV!$tqltu%3$bMP)3=NvusGE|!v=7QR-%bw*38jG2-`YgVF=giMO1cWF$)s5VumWdW_N){UnQ7q+|y!GBk^LdarqjQk`CKN>}pQ_30x?~jyjiI)GdW<;sBP0MaGci}z{4R<adozW)b|49OVeQJuUvVTLUN#ws2ij!K2Q}>*cZAn>XQk6n!@l**&#LL$}tVG7Fcf8wOz}bW}J^(oo0jGgz8j8Bh!>d@pDrjJGq>{9Snibu8TyDu(tqQH8iZW76-q1ZED=!yhtZf)Eb(vFkC_gPToIEXx?(Lyf7dNU#*@e5!+)S1l-x7EjZAamBmEl)sT`^IFHqo+8evb>-4b6%bYeX>VYD5hiR7`nL&14%VdXDQylx-k*x;%^Oy8@K^vI}(qeBAFV%h6ELmLldg!7O_ERf#B><pjNkm2+H<$Og=AF(~}u!7>tKgqhn$2GIPMt-`BR>pZdVX|TOggf{_GGptps_$cMvf_sCBm(eRFtE2}_jRKC5+p87@+FC~H%!$s3e1n$iz)?_M3jTnGTFqlbev!nUMCv>TZ(-JwOaUcZ|GGHO5>J-qin3{L&cuOhFbmX+vQj46;!bpS@N?l9?l)WQ{BZs8W9W-K{ohQ`eET6Y<ab}1xWA7db+!#Qq<!ErTt{jfY0rMl_Q+Dy3h=ELXc(U1wzac|7id}G;k8vqYSkPvqS1^sW<bD*wpvoKk3*4Ed@a<I5MNAbXEf%Xad2~QfQMO9bCHTkm0V_q1ZmlJd8d)gnU)RCm~n#Z#c%zLTb&Gi?p`G;{GJ@~l37k(-JV!T{0-eVaIw$K4C}>cHi2!>S~BEp%zF#{2J(*ZcC}s$H!$lgF`=v%@BX%ZYi>6Tf2C*`_Pi7rYPD<Du)y1nwhz&Fim#Nq8Ll+zrTbXT-R+0$1<@x&hi8q7+*SM^RGNxxv3x8DMAx1eOrDPnM*2$HQC>{U=<4&_PE+ff+1`CZ9%f%w<1gEJf0Ng4Jd(|QI5rRe3!QmfDg')).decode('utf-8'))
_LEGACY_ACTIONS_10C4S_3Q = json.loads(zlib.decompress(base64.b85decode('c-rk<O>ZMva{Mnk>mX93K77-3bKQ;Aj2cq+66=957{F^7FxH2$Z-)Q7dnK}1RWC9!GV@W=jCEsE?5g+uG9x1+fBv77fBW^fzyIyGlYjd8<cDvcZ$JL><>uk*xBJb><LSx2|N5W*`d{Dw^8MrAfBo%0{`TMBKmUC4>GRWHwGTgh`|B?^KYjl3=Jw?D<ip+e<aF75{qSkC`7-*$!)EjG``6n~o13pEr<b#@f85;O{d97=7=Hfc{_f+q4_^=e<Kpr0e^199`||n2pTB)MylFA&+s`N4&BNEHw*GW?|Mk<;r{SyFhv`5(Y;JE4Z#|#Cb^o~0t3X4>uRVO4PX%hg>~-es!5$7Rd76{Oq_4YQk#~K$z4@@Q#uN2t{~y5HX6+_#-TjyGcsA{L`tGO0Vwm)GH&e#X+!5Z~%-?@l9yeb%_wz+G|8BZ^;L=^r7tzDrxA`J!7w4b;u`?#$%zDSBvK^f10MAD0(7z8iyQR7R(eut6bv-nfhv8~px*vt{uiWVZ`wvYH*a^)FCU4n|Js7jma5OX4{zjj%-MG`Cn>=^E^A1DUPLr`N7sBBNHiLPz^0Q^q1#M)}q2o{9zNPwD%HR0&2!?QX!hkvQ=1m{O;T^+=?`Q7=`Vbqq!?;%-y!$1c^uEuh6W*l*`~N$7Q`hIZA70_Hvs>lduqK_uG;o3RdFuRZjcnf+Z^7IiAwO-*h(0a&aCdvV`SA6ZKW*;6e!l(uFVi!j)8M6F5?CVXcN}RB_P6$^J?0)79Ff_NjjMe97_b1}^!g9X@4Szzym#x`e?^-Fn0Jl&I5NV)!p-;@z!-sh0{3dSv_obx@58vaULV~71de^cAZ4x!{Nz25jRpGTK9G3?qWxI#N9`sj9VmNHCEHioK-4$)=bv~wHP=@Gp4`VlZ#m#R0OS7f$krJ2H-8J95ZlskU+8hJsY-CO7dEWlpVt3r^1TmisFezG=M4kfR%j3BDU80D!Q$Ufz56?a)JVr6yK1FFGGjjsZyg<2@w-!Od!=)sAw<Y}=}w^cYsuK47j0%(xE*6ckrAiKYk$COqLv3S84~swUGxXk&&5UwdgTm;4;e-d-Z_-@#{sV1AN&5;-{E6*0IP?oV@KX$2;YUA)?om}2+6naZai4#&T05c(rXOhDYXEkXAxyUkQgczX+MdoR~=b)!5d@q>E`|~R>%6?_yM#)jAEmq8v2qPqVZT%C<g7|v@ytmOi%(+_@ECRdwy$d(2-F!49a+<d^iN)E0bk+Sfl$vIYd0=K|eeZT{YwPjSO@hgPC(Q=zRv>kclw24{m8v?`FgMW2+$1+OwQ?zq@+c?yWJk#>B@(#I)KOF%MtwZ?->d?(hE!ESVI-<aWq>JEUPQyTeVafkq=1k4HeGUJ!%|-JJn5at=jh?@}9C$O2EtGO@<i$rx*jAxs=pDXov;!*HehkJE6r{f#`@w3z(bG1OV|PUa(!Tm@FYLtj5PGiwo|PtOg_gjm~Kju74iu6E>c8JO^BbiDV#)@y~yE+W{`x@gy&KPHY(AztR#2*gl9$E)H@Q(xT!V=~tYLn}s?;P&qB_9-m}npV3%?k4E_`S|f9ZR;KUdEDE;*V56cnS+cX(TTG%A8PAXkPY7Htc2I{FcBgs2V=>X0{aJKD)lxLQd7kI5G_8Y-q#WgRicOKzDtcA)kZ&Eq)b9@n@?%Hb7SR4#F_|T(|I^H)<lFdjyO}(#DelJ2z0)kZglj`Pm9bpV8e_)>4O4Jofbfzr_SUUU%)4snYYKXqAr5jvWry2ZW<d~`IZ;VSPh$FB4tW*bmj2Yj8_o@L{RoF$Tl_F0Ipwlo#|+W;!k@6WPIJ;<i-y<q+pyE=aI>V8M}UZcFaPM?roZpXH&ftNPz)lLu4s{_JR4oaWbkIaeN3qk&I?1zqDdKupLAbO!a(nmctref$%>R4PcX9e(J;{TU5}$Wr+{L_FKDNdf8@e$a%i9;0J%CnLRP|0vG_Mtq~gMw#)3fX8&R)4+XhN2b;h%$imGmZRM40G!TrNJm-`afH6;;ZIN*{U~4e^nL`!~sLu6_4?j!k-#=1mNd~W`JOVl4`xSD*`yjcCun$sa0bXNoBP5VBCKR?d0sL9W^GKv`fZMfZuyxAy8?LM|8f=;Vz^Eh69F;%PghDtmmD{hFrIgL{2)G8|x*R5WZ}9&3`S#Ddm1p@$?JxaIzY0jc+tSbPTZqtsgshL_HLK_pgGCpH6*zcXar(f^hLs4mydZ89%FhXgp@h`aW6Dv1Bl}>ckB#95C~2*E4vl0IdWZ`%K1zJjshArT8q0GZFm2s7B!MNaMSOVHoHH=jEo#)B<478)m0xR((qzoFrOmQShVK>ILiZ`SF`OB^Q~S#NTh2L=9N)x;Y{I$c8kxRXuhx-mKxZ%J(dzACD;``}tz*@9c;K{9XvLjK;uLmXX6*}FNN4Vf$2{eNv#0@2ard#N!*)2a$zfh;Rh2gek^0{4ky6d-0YQVG4Pu08M_2H|SJsI_ey1r^9m72bW{2mU6MAkevZ*`kuDi;t7%@ZA&z1BoewasutxVaI4W$lNk}#Pc->%|A2&?^(o=T~cb#$HOXExXhuOyIGD8W3`d#GX%LyPk)s`2$Q9R&sKp}uf9s!P<rca4fT%5t&@+WML<NFX)@_-2h?3>tzQQb$^(wR$r=KIg?!<er2!i5f?q3I$G`CT@;~7VJ!03!6Q)>OpJ63iY*H>o`F-6G-AL?-VA?gkmufDHV{ULVN|tsz?OE6uUVgo%RymhBBE)`cRz47id-f)Oibo2u!fI(5&~tdf%SMK_+CMKkfU1Iw)@@Y~HqwhRubLb<EdA-O%k_C4w%ulEpzX0i?^vn$U4FHw&2lD#sxQs;8XL7(<-;P#HcOAV1QW6A#y+hm>^#AgjW*$xoHUpmIT;)+c6IH*GD$q;hk~{o3(c#8_)JQ;R>Eoj17I*1~kL+v|YG>*T01axap|B+Jc!(R~|>xVva8IvWU&HB2xB?OmKbCfKtK-D`gY@P)%yFzAk(dew#~R{kYLqo?qcVkpE$5s{FazcvBO#lm0nY#q6>uXtV<jwko(;xQBcC(szktlD$k#?=}7t**&qozAuUWs-?Wnn_bv31N?fplJ`hd0W`4aUIxa(ml>chD#21?)G_Lr;%9!Q`ZKnJ#!uo3&>)YJG_4EC?-X-r64+NR&zvi*oL@s>hiXT(ka(6LhLYFbw+A4AP;QZ>%>|MO)>#$vz>G8uc1_ja^Qx9^QK2VN`^o?X+)(axzdA%Nj5)vB7B$5Ti~e7>*g@Dv`yW8b{%xnm+Zuy01;ZDo^c4vhz9-z{N^em9MT5zAeFiM3{`b-4rvmw=rZ~;Q~qmmrs~(Ex$1KXH;i)R4LnOSOjYBMvRd0XbewO)ZHpOOGDANA4&u-OZ&)?TG`p)S8CcdJYy?JpeL<M#j%Gz@g~WIs0_Ycdh^tyzS~i3YL9=Gw;)-E5G2O!^VkTEkSOic5rh3E;;=rQtwNCBS45@>RF4*=9FIf-Qf)p9HxGZ5ZhkHzLZMOr8zKZb>eq>~QhnQ%YqCn=OA*6R@`7&+&T8oNx&(EvM3Zl4+Mr$f9%n)8F%ScikmwnSPKQ`v!JB$Uy+{e@Q${j4JTI(l@ILxu0Bw3?{R?R_>z&stPtichvf^op+0M69KC3<2m!<XasTsaWU@i7>{cu<3-CIp<bLiMbaJVQprUKEXqvtW`6wU6VDI*9g%6bIS`kmMTGMV6~NPHY9~SO|!Ta^{X7JWMGhQ*8;g(xx1Kj(8uT(!qw8p3b6T)9z;9Fd~KP=haB}ipX~$X(eDtlRYmE4ci+nHKLf^!&qGvzgNfs4TumD4dIcuL%IU%*;Ug2F-OIYRN@@TSstG|XlhiD5uLOED;x6JDv)%TwKc%XKQL+)=9wsspB=M3;R)uM$DIg6a5Kq-W0g?3Td%JR+mF)~u?x6$+|d_MjKoMYfs;HKp~y{@mx4H4R2vez&M4I>$>5B8_l)!~?`W3^M=>*tTp<<DER0}h*Z#XhhP5hw7w-OxaV}bG9$FGo;((1&B)tCC7RmAoqJj@qd3H6U0-0hmp&}QB1QvhN-*=s?%w!aSA|^FK{jPWsP(2E%sa@zkt1SqZ1oholxBQH)<X|vbq3#eOh^|d+ay!Afofgp)$OspuASmxksx2Q;JegiL2}KA;P(hMyk?5sCIx<@xJdPjJig4SydQ23SrzgJ{y=1#z^J&?kKtUJE@t`SFY5!Z&191ZCY%!RrCIa#ynAut$9$gH4p=a9~q*t|Gg6fLLUG1gdVzup|ZdLoC)mrS(Q0iF|QAbItu!n273}hc98To8rMGrBbX~3plsp;S^oi0O6#!*_l`nu`S+-i<SOo+6$B63i|_1j|!@XQQ!^LK;<Fmeq9^BYW~R1+0AcAlLNgB}GJdK(Pf*9$?E@*0vpyk4E6Ec8H}b;>B$N6Uz3pUQj<ma7o1<DtM#Ds5nqDg(pNhCK(p#Y=~8Lc@IVSjkU`d1;|t3z9W7wtb+$1DOq}>VUCMrZbVD8ni=x7>?=Fh3t+T_+{7M%Q)Z}Zi=LHQ!9k6rU8j^nVG3(8X<5YIb?)P<{&NS=ZVo!AW;N3mbnvMN_z@Ryqt%kZ@N~GNIllrT}r7_N1LZWv{^+QeCjRRjGGu-_N<${SQ&o6Wd!Qs9KArgL^$0*qEG<9i@9tsmtfxnb>C?0_Ogpt_M)NNSWU1(F8mRKxXFruF;2F^X7Pp=JI&NKC=#_nq%O~hcXY&ff_sss-L95twZdoBjeys!r|UD}lhM120U&v82MP#Cb+9XhQe=-%{Zvns&KreNu_<4eq18j9eh8(>R`&pi_~>~DF6b4mxTwo_Q5#;<f^s5FStC+Wz!Rgc()e`=#Y%FDv4M7Y;B`tgSsf9vOeYFUIn`ZPhoou{@__iG)PcV&QlxpV7?XaqBfvtVPs_fF<`C29Kl2Qu9{qK(?bMQ_NJyGeeVt~j$9h5nk%$d7?)b;g{~YPjV%fXxm@WQXDtM&0c41v!))Mo(vL0EK&8vi2gU*bkt9Wqm+o^2+G<<{CYv-jnZ?;oSaoi@rPDiwhjYmv~#Fy6U4r`I3?rHRJEMgM9$3S!@5bXl%Ce9>g7sk$5zSTf{j;>z{$#X4p)9~&WiTBcNH(_bOD)HW}Gal5iJx(w_UWhVT_pl_jKs~*q)Y@q6Pp=4Rh?1OS$Ft~==WBN=-{CDNU;#_%<H@{rje5=NMQ(bOH)n1m2CW=!gFYp+pEF733*Wvccl7X(T2ea8-_pcJlF9;7&=)PBF#iGdf+`HKt<AmqQk)#2mjSq!#)Q48B%#Gvq=fB4qEAUU;yRZr??JFk3^nXdU}^(`N_z<4T(ig=ehsAlEk??GQh<Ujo-jS`JmNu0fB=il1L&*|6(lAd$(1BbW<)nHoz;Y7$O`8@gnibfh%#nn{x7Jv+BW6QFcttu`&AhVz^{-g3bgihouUBJN;BI0f*xMgy@igx9|YX!QN*H%lk5U}e^)ASiscCN?sHbdtzBX*9X8Gg@Oi8~3gl6N^ldCy5nqi;9lFywS?@BE*6QePc>+$3FInLED2ix^%pL&Qs3YU8NnIGpcYvr4ZYXxcfd}%}WF0;orQoZF>L-OW|8>iLah1ueM|g%=fa>Ci6Xe!yizsXYCxis+Ii}-9rZig1?%8X7CrJx1NFWjFJ%&mqUW1B>qL)F)8lo5hPi$fPQ9dYEf_Eo^Uo`y*{GQQe5)FrtkH(<T3QTKzBa+Y{6cP1{BM&XLE_L{0hCa*fhjmf2n}e1rB-qQe+n$+FnlI4b%hse*g6D4O8;?Q5maIttp}wfs;pS;-nco5`LqlZDv{FkdWdJdA8RYuN6C6T$LyR;dl|O3i1QlMIu}WMu2BSi0W2A@#*OpBZq_;X<GM4bFQ@+r0W$ZIhuX*{#5{ceW%?A!OL0T2+(YYIS=$Tp66+#N&e1#&La%qT;WhRAj$}tzD6eX4OqUDAN2-;B!3ouAVFHb2~`OwtphGVUiB`yIk^6W_T(7_wjy;=}Z$izlNdm+&SnxMoa5vT{KR#Z%ssk9y7X?iIhV3~K+TraugBUZOU^N!<!s+!^eK`cOYiRTijI-+4E_+=pbh&N0VlTi69@rIK%qNehJ9%#A0=|+<^G7U=L%_gfxcTHAUN9ZcC3MlR0R2f{^-#klWDq2kvwdIWcFoI+Lv4s0|N<;+=MIeoj!shUKb@$6vA`6cnp0thuE3BB_HCKYFqLMmAJ$9}QqiT7;)@SuMsYWT2h};kWZrxe((t_sJ>27C*F_ny@Xz$J&SasF0Uzw_&%7^1t{%lf-W@$&S2Misq&bLtv#Nlgk`fQUaH9HbJBS90Sr$XUU5~-3LF8*k2wM9r=qOYD~bHR3Ypl~IzAg9u)80=K!621H*4^N=s2p2laF{Boc8FfbD6bJIZf;f>fYo~>*3Xn3?DrHG|TgWtNZE?<?#67%3k+1+a%q_Pgsoii+ga$*-<9M~wDZJ7faoTaHnkrd`EJbUQ7!^ly`$UJappV&Yt)YHc+zGLIW2W%RslN8EQp7N|iU^I6)s`NrVt1K5`xxB`8z>s&r}kxCnla$_i%Zj?(lc3$lqA*SJU3^ahM)nh+6-~2fS;IU<8((>x1|gVm#W2(%tBq9DIw*_Tb4Q<QD5Q7>h}NhlFaAlRwokHMOwg#$2T-79u|e_L$fOgRH35r5}>%%!~z`lSy$58WhAqYk%U-^pHvG`o=nAzAvvJ2-e{U`LjGExe#K;jv;spEQl9@l*^OhRX+A-G=Vt=>t0^Ni!~QP+2sM7*Sk)ibNbEoZi&O?mND@&yU!Z=qWoER}LV7)!&Lw|5=mwkvrSijWJCQ~25vN{3If+>_Q{T8)A<B`h4wS%v8+j3&9$$5u3`Hf!SSq(|ktiIWPY3<U(qLxotX+yiMoz++7WkBM52sC?|Encp<=9?qqS>?CEf2C}DH>JM#iIb7S%OD#e4Lc7S|&GTt{77+QPh&vn*0nTeu6lWzm^`A<NtEcR?FG5x?0j{l%%VjGtc`SpNg2e9@TLs>@jQbv|>(ML$WI@jw}`vr-y@0^)nL-!!4&H?<=jajcKEgv4e{y%Tn2TJ0m~^3~LIJRDqnU@UuomOT(4bhiQgF+dh+IA1a~|uOk&9CGjgyDOx=TKwhKnm4#%yzPi*K11xy?E6P=}D|;PBYzlIfXbZKpUEgSMQqGigIa!AaAHXDNRn!*U9-oxdyTG&}_X`(Gw4_y*X%tC<@o{Tb6U#<W0zioFYl*$81*;|fVo0Y;<~4>YZ5g)b(E{7>_}dcBCNng7s+t<2U!}M(4sjw=$=vXPX=&J4X%T%-s`sbIv7!R)iOIUG5l1#=zLi#<Oh0KAX`Boh;VQT9)LLMSsb;9e&}Faa_M~E+Wa1=8)Yzk(bWxFv6DT8al7tFG47RrJz}CSF=tYHC1!)CoCaXljivUxq$Pd!jE6)&Qtif2aU2+z6E-M8)Y$(fj1eD*u<|OUQlW}q#O+b9PS@KG-?$5dJ$LRf?H~t!bNvfb5?i!)*c&Fr*dk@0{*HH$@P_o9qHA~7X)U@4nNwA)na>5k&8Bpr$V;xoet6lQ4q64itAZcaBDyh9F1Im=Yn$%nKZ0hCNAFI4te-e~fYK`-RUV!w}p(L9x68N(0rz~+vS23akacsVm?qdeT%(x5No$#bp2MSgf4)B@4;q5L8iJHa4Fxn#_w^W$?jB3Ovi95Mjr*UrLgC}x3l4Pb(&_W$h2Jw`Lkeb7w!Bg?#M7z`ZJaG5WcKR`4Jo+Z?lw&%1uq5h(lOkn{wI$0*vVcD@KDe?PWeF0`Bm>>UVgwM^=fx#vGDpqop%trY)!%$>&?zqwha?=W6S50OL(nHCJ#Z~orCMiS(h)B~AZ5rgXH+XAF&uyC3@|sTQuju=Vq(4<i%`O8#KRW}wUpQpx|Z^F2|RRwBR=LhJb{8e=7c2|N^R1%jFND=#{_fXesL$Ux`$E_RjS)qhzl<xXx!;>m|zp!@S0X295?Zu3YIDbkBmN7c&9HBjO+SJH4<Z*TOF_(0YP%j54RqR3yNgayir0!ofDS-pV$|X#h*X|e^4@)6VC#K2yrVJ4vv~&9MXNcehlD8tU`DoOOzAR6Y90g6j#Y9>L9Dpi_$kb)~HJ?S+lx`RN-W&Wwai+S#}vIf@O$4ixh>#-I<<-2zNq=ZzG^g*2#1pm|kUdYd5A)_lxC8^`S^A355(V2WO32`yd>r)k<|O>{&buC=oKlM`f|$NzO^Or*u-Z+KZG*qnU!7NaF0fMQPtb1J-0mppLnPckwhUb7-;B!h&k;2Bmx~umtzKp<%rCUx+YWUo)uPi?ocInjOmPrTQfR!qPvh+{P5=Y|A1P>_i1OMyM>RV(@4Pi`aRdsI#>*l(sJQsz%#$a^6Cd4RikpYN(W`aPAnbN_Lvb4uMb(oKXeGD2%(^1Y~=23@;|!rIh?6=7Uy#JHysI%Mnkb^_ZJ01O_=bA<W%(G+&9hwlWH&{y!+(D1#ZTc?L3DhZ$pNt?*Z;=HpVV`IxElMa@O+iq^{kHdQl}L%0QaJw0yk@7s--#*)zhA|AaXEo-D%syw|Sjn2qx@lxv|l&UH#j*wg6k9e}GkELlR1<2^IZ%mrLC)(0Jk%z{k%^7t>#se7UR!f&H#}+&;B26Q7L%GT2DmNt}_W>zFu^}Z#mC+>1&Y@<JljG-m8anyVLn58g)LR)JKkh4dEW?0=4jn)zt4tp&T(HAplw~$FrK>rCAfKA$7uZnClSv^Fu__4C#c6ZNLS^#CHMdesnIN^Bf~{ixMwOcwrHIh0kh3Ux>as7&QkIr_c1k(RQsTIY-ODU87YY|aiD9j~RSw*>=L6ngq+H(FGEc-}dDna3fyXJpanZ~pWtm0OA9*&QE41hZCxo7L=|+hlwmhQ*vHeSzZ;CYbcB>sa$1dX`2C5yt2wyCshn{pZ^OP}{1C}d;7)T_OY`s1VuOlUChEh8U<qk7!D6Js*Ti|-p3s+NHL9wu9q?^}zjoJwDE2UsW*+CK3CtIEueW+dN26qu4+SP(Y%(6(`($NI&PI@w3M+#PkNL$>Hq=pyx3W2B@^4+RP-SRy~&+l<O0e$MON(Uz)YO#=jF(F{qO@OXb@iNu1(@0#-ebA;udYGF&kJlx>0HJS5vaDW;smc3N#5N_eR!+x|z*W5LAjrk#3A?<QiHbw4Q+Z)}o;5n6HmQVRQcue`T8>jiP%QJw!<(vNm2$HKe|V3YNbIAA+rj>q9oFbl16a(rq*)E}mUEIdG0)6BP_E3K7P=Qj?u!Hus)aV1mEbS|Wb)+V$cdXRO313AZWIBGi~|*g-x!6^5m%u{@m9lvb369*m_-OoQr5MGEUu1?EUpoDxTX}Qbv+$bCs#*!S?30~YW(L=?M3(mr3_<+nbopgT$GQZt}bl16{uG&k;U_<vt+GqieW6<M--hSE?Qari*WLE>W#<Jst)qZ2Nd*DWArUnVNO-L(EM*Cp<=H9ca?iHpu}lItC>SNS|YoH#%HRekyY#+5Waq&?_yO?HRihova~6eCR?eC%WZLvk+2>(A13F%hzSvXEl~mwk>MnX4!Ta6?oiPT;4V@&gi;{pLq?e{+i1?!dES&}hzu{;wvm`ROfj>NWWCJK9>>S{HkbAFN*TFX&1kVkCixleA6?v(JEpGHfKI=x3+mBeOnKE(38m?zod+TiG@pyY)r@E+qbO&od0}{Zf|^u>6r@f_7nD=p5}x8uc-}M8aP9-~DR^u2^mtkxz^~{66O~wV+An7>i2h83$H0lZw8Au(c<6sGiey&k`!$uy809Qhw37EO;fT1@RZTE5l9AT|cN3^9NvfK8+(oN#GG(%$-dYbiGPe@|Id_U!=3uyOLW@i%%sqicIi^(~<uH+M=7(q30f?HQBO%<tQx8+U2*DF=X&%c=sXwOt$fO@=kUdFuTb4^s%5<Ww2O$^fq~P#kpte+PC_Us6>^EJ<fT}OV^8*4LCB3dAbQ1z$_{2~vRSz_AGq1>>!hJ~a_!?iOr8jZthXsSx!jf)*#XuArU7H-}@C1UQbtD6=9^<XMWz#Yus7MWWPQ`37VPkSNo?$sT#2GO?FQ&$$^N*<nP$&&g16*|Jy6g-vJrEVOlzOMavMKsoYq!{yD7TU*qFpSJ9P+LnS7D+6fFe|MPziC?W&R@jWowJXj_?s0cOtDN=+<$?nid8xXt7YLTkaV{QhDq14DQlSmkt}*44sSDNkvql6;7dt4G|@byqKe(bfcMS&^KB=CRB`4tz>E;N6;|xT9N!aq45_bjg)#WZfp=8XK>!zqGYJQ4hcb&8Sq2p!TE39%t%2|%>@dO<%riyoma0_MwUTrtXS>$mIcJw(_XHk&%gn#fvI^7zR5!Vwk4e7Eji_kylLA?1Q6Xc6*Kk{t0{_{gM-N-9<ay+cUEczZAB$AdqBCEPNWu_ua};#;3D8gnvcLkV(jK-p0nhHE*=xwT3>D+9;P4s^3l1nZwiHH0`fF18$OKuFVt%IWu}F@2O+eCv@Y}^v+&wxfdT3Ap*mUzXYwsIt8Zg+t(sdpDSpGnCDqa~6ONkX@kwq>)JuftphOY~x~Z<QsKxP3Ie*E#a8G?-+Mw0|iL1qPq-mv~v?)W?!5xFgH8R;`%NkhL=^Z1Hw|A#*(dsXDcGd78XJD1XD!?2DT{b&cd@1Y&B&v3Ot!@xi-uv<X?#mG_C4z;5jML={U6m}UKzL)uxCy-yyr4ZZkN!&Jz4v`-d;F0*@g=)SUh2zolYTN082gnjO2zu=z>6FE>d5qTcZ_HshIh{XL=FukXEH68f=dp($U*Y>f8tM+hX')).decode('utf-8'))
_LEGACY_ACTIONS_8C6S_3Q = json.loads(zlib.decompress(base64.b85decode('c-rk<%WfRW5&RdPc~H-TL;A**dM(0SQJ^Rf*1}-1fY&f!tPgA74F9`javt4Xk&%&EHRN!ilLn(<cfBh!GBWbZf6o5)^KZZY^4r-TzMOsc`R4ZBPam&8J$%0J&o<|0fB*TPfBo0j|M~jy*Pnm;$1nf>`uWS*`<uuA)joXp`NyBGKivFqeS3C(_V#Xlc0Mb<{`9`@KMwxmQ{TV)`t|yKfBkTFzM6dfLw|es;q1KI|NP_q-Mi0k9}a(UvDy6heAuy%H*f#+`QzbD-Jow@&er{>hsU;lxVwLN|M+SD)#Sr?AU^fCw}-dRr*GXoZtyD5kl||&pQclR8ZddCIeV~&`<6V;NjK{2_E+RxA8)VU_SSf!{_Oq$ylv8M^49I249Bx*$K!V&4vS&b*X>LhKXXU8zn;GTusp6G`upi3ntnH4J#gvHri<v)-RJ2dDi`PX|KAy-ZzjECQ&|qqcz`FPbm-sP>+RCq{pe|D4!Rzi%foP$FWrs8@K^41f&GUj2keAm1(UaI#~zH?U^t2yD}STU*mm6M(2bru-Fb&0ET_p>mz{99fz4nZt^8~mbwL|hbm;h#w`-|Bmhw0LJc1$Io-kmJym`|HasQ6}hp%VvC-fmUaEEcPdGPj^bkf^CpH6s_4($GR@TR8Ebw9koV<)%D+^{B{!!&S#w0Y|EY>jN+XK%sO9w9$1%!oEEczbty+rNGI>HGfv;pX<{FXJ<z(cq<D5?CVXcN}RBcDMGRJ?0+TJ0g=G8&~;q6R-eJdi@9HciP8A-n(_}ze<|~n0JNwI55J&!p-;@z!-sh0{3dWv_obx@58XSULV~71de^cAZ4x!{Nz25jRpGTK9G3?qWxImkJ?R6I#BkYO17`Efv9ip&p+{W>Rew1cyb>Hz2$)O0F3*?BTHk@-~1(TLTpRFeWAy>rYgbBp4qVe_O$j-lka_CLoHO0J8u}+wnBM0k74v~0*ik=_3rNwQX?IQ?5dRx$&CH5f9v4Dir<}L+iN-(8bXAuSKSHpeyuV#=tY|u7H-FwP-Mhu^4cFTo2cbMOooI#Mi>17^>eXNf?hd;;X{UzgLevL{eFO}Z;$=<*jM;i9l&Z~>e!KY7{YfUr)3yGF+%d?y9*DNxpNx6lJpt_cuHLW(zA#%AV>_AinO0Z)oUGDcEKBC^Zxq&&sN9U-S`2tK#XFeq1yK)IYh&;sG%5?gHy&J_hf=9AcYV5zGF{sjSV_7s`i6294Q|T0r<*j*&WvCZcq*pPkGP}PefPE@O=XVUB_Ui91VJ(fj49#%;kein$$P5;oD<tL87H+Ic<M;`MBLnV`_<sk6pyH+8QyR9`3K#-}U$RKLSf8g)q4tGT#nqn6u_^6KkN+h;DNPH0l{asL<URFe9f>RQ4{lk%cVqbSx8VXq^nPrWnG+L6xfYvH!5Y(*4J2INR<<9&B1ner*`)tnyB#BamDLR=-1EKQ%LJ5u#5|4b6mD%Ug~R-UP08<Z&68@Mv_rZ-K3s3X@$#u%l(AT{GV#j!z+8=GX|tP(jD5;!IOt-2-DX*9t=`2AAOa?(X(6Ee4ua+yC57(AV?v-C5e!JNWasw}G#vqf;{n8AYNIXJtCn)~z5LyyIC3ujTzjh@c#dC9eeb56Dz%Z78Isi1{H}d`!KsB^auT9;W*)b?m4z`spHN5_(&FO5>fql^+pnB7jY&;n-Lc5z08=OpOx@s&_%4^W}7-qi=dzWVQhtX7ouP6maU40P-|-Cdc>!KFP$qJ(d-95zLnDQW3jxY;56MUNB=dY>tVPDb3N9!&?(xMGO!@*}EXy)Mx{^e%W=VqZNuj?G2Feb$OE;Kje^tabC<LlMOR={q*dZg&^JAG$YTZdMS_s1IYG~r2yIo=KtEssAk0Reej87G&}jFHP!>$K{UZs&nIU&tl<?1|De(UHreIpPCT+i1^ru=_z-NrmFuOIZB~Yyrz;D7@JE{26Z>8O1HiO3LgQR^nLXF+U(Dp8AUEk?5qJh!xS6G`ypoLuf^n1QoYDd?=83Z{GR_8U4Te8+$btdYxt{UiXDR)=M=CAJ;MJ5zASZmkKrVP2B)1FuAoVQ3E9`BA1agLi!qO&yKMQ#tiS!L{yVe<OjdK0=SJn^>woHFu)DdTn${%S$A)J`X?N`iF%I0|lTmx`j?k9L>@cwXf`={;7v;3s;mwu*S4M@J-(ogT}MCd?5)`#($MRbb6q6@<c9K5Y@`oPQfD-mpYLEI*kpA!s238|;Yl%oPi_Q6aa8p8!pQd;vI8p$N|5Eo{6l=!4mF*hnSmUAC4E!{RGfhDd*e0bJ5XJD>N)Tlhiku*>#zg8Nh$(U<Nn`M^_-z&C-?o)7MI5T*s_Lcd6Ip;)jd=nqC3Fn?`Wcp^UT1U14oxPYxtG9=(cyM8rj#b;?fzv{v6?Y<uQ`mT!l`kkEovAAx^OP%`MGbh0yN`7`Y=;w@9OgBxs^yJAq`q}~q*Sx|fS|$81~J04qbqpf3+qH7zta?|j^UmIv%~Yw2|YI!+0>nN*Ii{+jF=(m=Sun(Kg=V-R;KL9hEfM>k}#PcU#{Xq2&?>&o=T~cb#$HOCpOpuuOyIGD8W3`d#J@A_ASn{sD{_ecoY<{hx)?ds4h|e-Zm=YD9gzrXzOdbAc5Er;F}eGF=z;KNF8aB((29d_?#C@k$V!_Bx)RaDik<%inuu%TCg*1Eo}DGS`S(qR;aICTE_{xnLrX}d8aU8CKQW_NU4A%72+#ERz)HRrr6C1>9ptYHk8Rc(uc}ve1=x#Pn}a3L|}rQLbJXN*0=3>9ArZF`P05HsDpAcVe_(WG;A(}tYf||>V|IbDiL(Kl`IaD2_UUDbwbC<+$>=Fs~m?MsGf2{V+?WXLuL4Efc!{fPCQ(P9#X9v09h5bO@6K<22~g2DScvwb<@@|Oe!~*+^-$JMU1u9W@_<Av-1Ww+gg||c6$}@c%2+oM(#xtnPj;cFuHGJ5qB4DMP~!yv4#nTpuOFjO@ckk(7p0U0ADzK1%vLmsh4GlV&Pv>G<ph8DTYGyiim{V{G|z4cAdZG**bD%U-7&!98d1m#U>N}C(szktlDwihSeF{t*+5yoz9i}Wt53Ynn_bv31N?fplJ`hdF$-exD4zw=^p1J!zBkBcY7Y#X=GNw)Rlp1&zy(D0<xIp4lg$i#iVGq6hw#3YK~|Q%Mf=?UEUT^I_FwOh#f|&&PZ(r<bmG3POP<1Bom-E+d0?%8cKC22X06>Z+g_DWC*mA22^TVLU^xYlFg7FN#CV27dS5SvRMozaZ`7oT^HT-CL6IQAb*^b%4t;9>qa7_z___DBl01LNDV2?&F86B59g3B0gErAFEeGpMrW&jU7Bk@mw3adN8Z4*WW!Wd4k^2}j7P_LH{8aUuqHD!1mGy{JKzngMxADNc1<RhH3+@HjIUo1=E<X36Iwwro{s?fg&yLnS5_^X!iXQ;3oL);6xR&1j_EEou`{`bLKnafnEnwrjRVWVS3R|pG^7qP;$Yb?yl6dy3zB8n;<6;l92PP`xZMsYN-M@g_@R;YB4YAoiWZrVi;&(`3z=!_*IHDpdwzyhRvN`!G+I+>iH7h>nMKm;xB#4n{;@F+-(oB@=02XbSMFeyzO{a$h{GJ~Ns>QW(W)sN5}2nW6*xE|YcLMo9AKJynTeLz%l^w@doCTQ=J;3);6A8fQxgo%S)qD<N}ekt;xCHY#G7EcN`e+c95WF14@nP{^PeOg)vGPn3Oca`q=O+KILawJeiSh!l}tq@)RLQW96I8BD8<&@G>vpV6`OZA4~J1ITtBaley_-V2hvvphBVpq;?S_oQIaGo^L!Y;tH$pYvOxoKghWkv;O&sEz{++tLI9YpV#h3Tw&WzE&mA;1K1kx{TBMbY_+$}Cg3Q_yV09oE#|jfpl*Uh>!<Og-bIjvDgrU5dq{Ok3sNAd9*M;rI>C)I0z;)cu7eI^_BVE%(??V%Eq)3X=L?W^0oL;v~Hzw@dgDzy&YN)(eZ;D<5sKHMUj5jar+7AkoNY4Jkkg<3b{{OR)G0K<~G%ci@0vohQzyPIjlBF6%wIFJh+tp+XWShwxi(Ft5xBy86!1cN^lTnErF%=5xh{fxJ>S0Mu2t#*bZLPQ@%J06qq-?AukApD|bq^7Ep&;kU?F6TNS{ziMFr0JwnS1RhEYuhCnwfBTLOz0r&DT<Xm&8S-NR_f+qA-V~D^Xc(UP!d?T!2Q~KB!V6uH{s~v7EXP1Ic4w^>KARiTff7;ZotuK8)h=GlIqmOD#iNv91MirF1gDKJW?Oxpa8yq9IpMk{Xfq24fO}JrRR!LZ5Gtsvu3-3#cxhLTg@y?8C@wzB;`SIZscJErqsjF~)O&o_yigSCtF}&W&g5!bm`c8@Y}}v+K(wRI&Y&ZmeFrp;`uk_^Z^)(ML<>Dln#gGPJJ`B#X-I>qRF@qA>S*$HSiFyFad*?Kh#w`EpZ}qoEnF8JT?QBa3nt3E_&;sUT2+u|CEVk@2=f)JO0wV(yE`7_s`8_BSQ(j(NkW0f<30lxkZgNurWxB$<p@-4=q3jc1s`W3KlO8D*?qpjM*6CxfysYdI?n&<++0>_h56e%efQz-e4ol0gyECrTG=;%xHJC}X4uZ1Ok+$6ymJ$Z7ukdG+oWh8oMO2oxf>=p^EVvD#E9rkl>uK0*vJS*tF|5hfqJ!N&e7rN34(hrxB2XJ|VLS3KpqX&8YlqH%e>Cz*(VBdq6@i<rk%fWj!R?|{6$RHZqB-)Q;;l9D4>om|cnuRw3u)ZTTQKsdxdtXRy8M(4r-Z`_?(L;{Oi!&y*E3G(^<h=|8|WDZ&pfT{ef`x?cyr^9HL(TWpte*>R1f<n4Ok|<%YRK;*2@dX;^m3OM@0a<Dssvx<;s!uE%|BB!uS!yhd>ga;f=(PEj-=o#0GSr$`M$QqI*(N0|axZ4rKy{;9HkBMQ**!Hn9~Kcxxh+SBt4V=bmnB%&efG#(sN!n^KA=fG(1^RO`C-Besq;k5DPgz+Bh|1@YT6;zz@@s|iM8sby3xtlyi&TbW#?v_NZAQ;VAN)ykNFnKF8b?|4)ihWw$x2i*A!lx4e5tNbwkjgt5ank<oNhid;_jyZrXh9Xa-(_Z6B5cY{xb*bnk=uwa1|v#EVcSYaUjKD^RTDD0Mb;iUF%>VMc$Fky0jv=at52RJy}kP{81l62_C6>a6~&8c^?Bls0GdX^ikWTn>FoXg?=%%on~dK>VBiL+aAdS%Q|PFVaRrR>Lmn$_g_<Q1`-<N~72@$^gQ2186!!JiMu_40cPZpkOx=q@-ooo1O!7otb$Tad7}(=YzFlQhlVPX1Q%y83vwVLZgm$Y+sO#NI)1;oQXl$yegB%?~_0WDGug0S&1TP?zMu21y=%B<2M_NRrHS}+<#$Ye#41=MRfNQ<8_!OM<c0yTpY3VWN3mRQa(itn~P*RmK5!S9=uh?jc6?8QfbS%hAKqO)%L2(1h{9*s)&P>5ou+C?F{<;GeUZVGR0Xf7?7Y55N|uHia-O0qS=*W6)ZL>ky-~jb0<X$@~IJy)h1KB6L{geG@*5(*mr$0@O$1OJ6<yIq*8U*)XS~COR6ukFNo`(I|SiS?Q5y?5)V<H+m%kglGZa$q%P2tv9|=*uA*qK8ioES1i+Z6wgA*+D@G(p3-UTSuPQI8DMwPohxd`M4q<lfGJg?96xX&el03x97c5RAUh=>R<;wE1IHdY1UrQFkO)SLgRW=Tbt0eSsXAvMJT9DV#yBPjO1yoQ$v|x1%e8CNGI^0aD6d7uAi^ZuVRFsQ*b`rTuEZT~hg#M)r2o<unu%y6CN2Ov>u7sWthgg%!5m`N8wN@;~<t89z!G|1Ojv+FS5?zsP3R<%I{5W}AL;gs&DC;zvjlC-D`fhcq*x$1ke*m5{OL&qhKQzhTD#<9&H&E#cZI})5N)G}I!7fdB?lolE#F;Hs6qZPN(`xBUlFy|pASP;dw9~mv&}RBr=-tX<&M*SBq^x2!TP_u=c#<yDz;dn_4MnQD5s+-m@zAKohcq;y;mptq8M(^x07M+Y;r)atM-+c0Hz5lxA45ITqoHXEj$E#=g0LkS(44vDAbw7{BaLeSoISb#xIL}@PDAe=4bqiiyROpyI^9WO)qk1~r-UXE+uvS0Y6;C=kXDT&SPO*#Ld&f1f&f~*K@%X;L@iR;UlON=&k0Di86Wn-qnq`Rs5Melo@teG{go(1X0Ce6g6^bP+mu(4w3JxmWI3tH(N!f0#D)fc6w6y=I&lD)h{)~>D}P$aH)fpk1;s!Q<9Qn8F+k!3bj#z+qstTEOU3>DgmjFgLxCL=rzUB}8Gm&Ys&#dam9lm`Y(d1IB56<&QJ*Xb5!b)r{<F@W3QNSya_pxP)>2UcCBLwV6pXHAtO?tQ5;vm7zfAE!sQFIuH;b+1)fLn=YR_dsU@0Aorq4(OcV6kFD&U)0e6h+O=V6CWAqi$RVrUYMz|l78$w~nY+?k8W!NvEplis`T{p6$o&Bk9&3_Aid;UOh7`692Xp==B=Cmb9SZ8c~NleMW_D5-e?qx|mXkA5*+`jw;X)8@<q<f3}z8h4KTx;7a-BIPo5;;5`)lEkf6?$%@<=b1;Nk(lRmwbWZloc<kqWC#OXP%d$72#V)Qq^x;h8-O~b45g!IDzi>V7Hv~P6YE&X`q`mVT%D;VBvrA@7Y#8?1zn@z!loiQt7By=I$Ah0D<1SzxZ;)7=xM^a3gt1@*6VTe3mOA;0R$+N)+DmEL{BjW>xJ}PeMCuyUyfQa*KH>_u$yTDwJns3%%I4Eq6kxP5?E29OnF>KP(%|M%`F=4iJJ_VUeq_1F?d>)2#<+You`i_rX>p3Cd5h=O=bKQMJ1RVyS^lp0?EZV(`?YSq)n`^2woP*ClBGTP?|?lHO#?@+%W`<E}PENOuH&rH<qRS2BiKZ{F61!t7t@_ZJrU5!aFs{nFF-gA~X|7;>tzHwp<uKeM}+QTGPyn4S-g;EF!gXHN`PluW91vlS9!|dp3xh$E(Y68L=c`%Pm6yk4u+vEzvsJ3<WAhqmgtpr)Y&cq4+#&vZ|{!97Bf}sN|hl>R}}eLOvK|=(3CMx)PVNrK;@Ub(3$7U-GMfTV4i10Z_z?>OOgl0LI7lz?9Z_2|b^^jzpO$4Kl!#5WfJ7U<(HSLiVtBq`!9AVcCMgR4(GNmGi8Q5jz1bcy*B}62?kkxZs7W3uRN`Gaa1k>Eyw(t2!r)#<8lStz9bG%1M5PN2?=KpzjD(5vsk_sP@o$V`a%ZuXmb!ZuNw&Qj{M`j*~<xRK>RJTy{Cq890))a^IqfoSLIq!6=_cR_c}DCP?S5YR1?#;VA>}Xu)81g+yySvkWMGN^`r8qTn1E$L3lKrQ}s=pTR(#1;yCEaVekeXGz{=oDaqcC5~zlg;~qz9E)beWQ-WDAk3$)6B+1Tt}lv<LDhSheUjgAUESGV_7k8bHj~Ge6Qq*<&;u!1O%gn5k)h(unpH%E%p;E*R;-jnTQZVHYCLcJfq1%JH7`YlaT#mU3rDT{SSZ0Za=9NSR0`ACXl@Y!(C{4tRw~s}W&sLJHdUZOBih94%fQsdqbpFYklfers)X6_Lsl0S*xr){cIKBO0xN<WXa0lR(zr_JE3Tgevj-`EA*1UAvik_6nyAX9k(okaYL_vVCz9!`H2s&=CE7|rB7iw);*BweyA>Z|?l@CVpdPxf$(|@wFUlO3YcKBZs1$wjooh;8)ImgSZb*7zOfX+#mB-Oaa;E8`?>3vo$;y;;l2m(E$dA?hQnw45G<m>;DmT+2vH(@hq+V1_Ht3PMG<C+$E)ho;%<<A0H5QM{saK#aRtQSUBN7wP@YL+QkBXR;TpYX?xOqU!Lrn$N)8}&MdaUyM*F|}M=Zo1-B376J46X;c*1Zl^E@H4yTE?5{le^XWf+wkxEjIKTmv*TFcSUSxyc`4IIL1miqMo@|&2DF_w|<3;*VC(L_b|H5tuU_lHQi?lCGj$XaRoLug`p^vA{T^+*f}$GWrE%5Bse(La4d*DECVpDXXN#S0k5J^2}tiWODhic*W<q-j4_vI$;8>pc81a{&4z}HJkqL6$3)(i2w_@M{AuZ!a3z{pkI0otd(73Cws=naGgrie;U96&qaK8VkeZi%Rak$HQd_P@WL#y-S3%?cNV`Nx5+__|@=_~kkYpR_c_ej8ZZ0Gu>x_XM(fSgYac>q-zT$NUnZi3Cv7Drhe(-@q-BEYZYf7w%#3Ir4$<Q3S6cNW^Wia2@gVB)T39L4y)MpKuQGq?-q3QKcLkKFhG=_KoA}8GhFAOtYYLzBnWdu;De-@hJS!fF{Vny#rpTP;MlvdW$LSr*LlgfxH{46IrL46X2G<szX($M$3*_^7?HWUhFrY9Xan=}{$rjBsErlE|4cS3unxrOLt4)3cJ@Jz+w7&S!VyC#n0q|TgAwgc!<rT~juBB7DQVKGw$X-H!s^9VscdgvzvSTIgDbU;R)$}nhEe@i-DvALQG(RIP#!migG?lQ@fWDVfU+86ZG!wgqVYl24GOIR5bz`Rx?b0zmv;d2xlUMyU~f?<SMTATl)%_qyWV7CmzJG5;r&!V(_)d*-3PeqLwU5zzJWlNHyjm(`!ElsTAM5F(PY=~4|vqt@^f=b6MFTFm2bwdfrj+%nK4i?S~j!&dco|0OvC71T`%;HR;&JaIPD!p0S5Bh9au1m3{DiLBC!lfnlBvwtmLSA|7RHrBV<Ln~=U0`)kuVO7FljWr5v{WQk^1;t*U<<-!S15=}hW})zM|tc=S5_Pz^4Yurn$#@jZ4+vM>TF(FR#2B>=0evgLD7Ieg!7WqvP-0j(L}?^2cdvxRb-1DCWv2dh-4Kc)`SQoj*(dOJ2yqqE$vl#0g9Q|bg~WMor&V6#4k!|TDU@noQurddqa2UaTs&_#{iWNE(9Q!L&2yC$efbj<7sv|dZLguPqRrVx|%z0vd|$Ie{f;JF47Q<O}S`N-wI5VN2OGvX1EVKxG7w1q07&d6Mm6Op>y}LCKNFbNvO02g1r3wm#jN*y5&GsxfvPxnYF@sybx2_#@Z^B&rngoaXkE5@^QU5i;v`Gg0D7}bw!(J!0Ko~wNQIStx+9Pq+xz8=Uf}_??QnFoloU4s~m@=X>~P8+sU08hwR^?bf>8+l7)B@B*=sll$yB9R4m`Y7bH$JO-~IQaTirnMwX_T19I+W4|_06iUd{~a>I+G!oW*Z_n`ZarM*Q<<Avm(x>=xrGgpu^0x66;RJ{wMJWi>81fv>grEF~%t<J+r<(p8BDb=Fn&T_om>$2sBb2Oh7dTJpQ#>OB6S!X!6A(PyX3V4uan9x?U{dfTdt;&N|C^w_#n7rR5=8ae^QvCz8f-ghV@Q@AA<-we_!cYs;3#&}(7&(rMJcWy8w>Z@^N^u4+T{uC7pEbtmB$A*~Gr52u^QxV*sst8R^mn3~5zrW-ZgECz)y!i!Fw>-Ip0&j&hgQmt?fVjW!JV%>2miOO)`xzbN78?FAwdhj?EELJdp$dURk%`J`#fPcmM)0&g(NgvBni9JsYXJ6i7fmvtxxd}RIU{V*`;vI5wK0*fI6U^iz3mQl>Ula3RH>Q`T|>l)iE@6gj?rd1&kvj3;R;qe%{2nAbTP(_$Gzcssj8JJf|$jUJ|yrXq@D$FH8@2w`_i)#$-s}YkP6!>e7^ipLn(}n?<-E8z_sg><ZaEvAwSlFS1-j6-80F%`GjIX{}0s8?Z74Jip&ZWq2pqc#mA!T-_7RCnxs_g**+$UC3DDRTnH3IR_i`j~-<md3@AmK1+(Y%^YLtrK+$LL-D10i$ycYvZb4sGPA6$LZe$L<ajL!E3QR>QTyySn;K1zWpx(%WaXkYXK!SR%aZI>E*>yUVw|Sk^S@-F8cBZ6&p-_m;HgG<RE^ru$+JKmV0pu==bdPrasHL+a^P<R%5#e&D9>5;-fnXNXl(JSO3zvp=94W+tH{hHuo$Ny&Rt)X8#%e+0|xjyL6lRqH~mW+Lilp2jG#80>vX5Q`B*L<sZN+o<Rn?;!J@xeR*modD?p?x$E#=zJzmH2x?%{7{3=gY7|m;x=0cL4C|KxtMa(YaaciPg5WuF&-9pW?wdTGGLq89Mn#r1?&2|F|a&l#C29^==I3^t?=`Wj}K;^R0ic>NcqYvvDd4Cd8Ft6f7adJD==aVaM#xsZ|k`r~Jy-EUd-f%wG*{sUo=303KmkYhJscX&EiC;qdit_A`FD~T&SrciCk}JB03OgX?%kyhPszFP{jHHT2acwDrvSF*8@pXKyyhJZ%5z<Q8&a#8SdX`b5U~o><Y+H7ucu5;-dZ&78rY4CN6lEZhz@M@=T#LTYP%dR+dZHUj*^CxFsH!qL1Chi_1B3#^-!aSb5a>=rIDmcnJILdVM9EV1Ir)8^NQz@A95nDPKm&^g*==i8Q{9c%y8uH%lmje**xR{rt0mWlN`(S2k{dtb(v=rQ=#t@0^NYrbd>Q|$P&d7vYwQ$0O9-RUR3>Z(lI0g#RjQ=6rq?xXer&2DE5$##iD*tpr7u$rR?;iU#5Z~N3d?hI;HP+1&5T7I%mi|TW2LxXNa1%MPjuoSprRKPc!;--Gh}uzBT>?Fbc{=(P2-%`mF*ii7Bz*$BnnHU(i!YXla^K1Vq2eNtNdX6%M2D-c`w+klU-c;hfu4gu_`~ZU1}cz+VFCw_`L_>4x(d3-AG4iSca#f?`4F~Se=ZBNHOef%myQYBLDq_X66*^V*OU^bSIm1trXfJ?oZ4TcFYgQ5M>~oKsIB}7$qOJ81P;#ukN{xE+#;VqN99$dZzO_g((1?z1sZ07-Pi=fHZmSyZgJ3#{H!A)x6OOM-RZDv%tl<Z8J5!;Em4oR}aW*zG0H}1^&-nlI1(gWl#<VxP2zSu6!lv3az&jmpfLv$%xKAQ;gDKgFR)MX0NcTH1VveulpTb?rG%%3;meJDG0PI6#j0VasJe1($YCTayI`1P`HkW')).decode('utf-8'))
_LEGACY_ACTIONS_6C8S_3Q = json.loads(zlib.decompress(base64.b85decode('c-rk<%Whm*a{L#rxlld$kaujU#uA3z6ewwkaf4_y;4uss<3-y$!~brXDpuXPCo(c3&nc1`a91jp?mh3585tS*>;Ihm+wXt;{cnGq{L`-|KYjgp{r<O4SD(Lpz1^JLpPu~t@BjI)|Ml%J-#-5R_dovQZ~y)6^RFi#K0f?a`|#7(zy5ah%g3Luu1`)+-rd}toGzQMKY!S4K284cd9!){?d!V_o2xG;rx&xYf8Jc*{Bm--*!}#|?alkI@4oE+$NByJ|DH}e_UYrhKY#tSf74>pw_i{0HlM#dwDp&p+b<s;KJC7meK;J5&ztM({aaV_w>~~@@+#1f>1+3&=2L+hFne7%d$5PQmORYK;-IhFUy*lxy1sh1iN+K4=kY&)x6Rs3-n#uS)A4ND@$lU*`^9k3*X>LNKTAh=b2WeeetBGd+1$<-(fqr^)dQFAa=wT@-+Y}fqIPlq>Hl}e!8fzsv8ika=Wu{$qqOheyQ}TeeEiY(ojK{cHJAJ0YG3*|3e#Vu(*^b)njEkbniWjmvK@OcW|QG)W~}{<K4aT)r$cw}-1*Mi4`Dk^!Ma=sha1=o;nB*^mV+*6Ba055eDWS!s*k1oO+Jrc2)8E;n4@go^g-OcWB1|P+4~uN@CI%_?mZ9Q{*q4m*yqy;AJT!x|2uip(C4Nfp5d{xTV)kklgVLfTp(kfIzL;T?fc{{nA;=dr;QmgrUmbAuCF)mzWny5&Fz<u*B}4o@Jtvqc;%NEOQigcBhA6%tvzW^xQBL*$n3|#RepAFSb#5j{TuT;@8i1e-KO?mr%eLPyT*K+7~x>yR{RWLjKDpCd$nEKmYK}^Fzs#D$8-RJV{aIw%vFJ(vInxUK%deFGLJyCA3OZfxXDEaDjrnH_Ek0z_09A7C!S89>#G1y>EoccY&Z|VxZgjrH3sv|-vTGZw#?gSJuWp>32yephV|>y#y?HI_kj(yRzdE%VG!F2?csa~qc3K#__tH<_68v}(s9VHTIrCi*blq6P7W;p?iAbJ(>ZGh5whNOC(!$~%h;e7ZDm-v9TP&4j?<L2-!Pk~<v~n_f;~nT{T}s8u~C9vC4-SehR(q|hqC^0fUDQXzCQK`e5?*&jWBiM$U6+-r;yW`4WI-e`S#t72g}?!4PPmGjRv057l6zxq6!G&p;Au!NmRYpk!2TrFg72qZvPT>Y}}1+pao(S8x7U2FU296jztf}pdFkx2Du{>bO9-R(03jC{#I|$kx{i9l<7$2a0tLx4wl`1jXn;_KH@14`u>UNs+qoTVxa37%$%b^?=$d*N`$$6a7&YVH5*<Z+Y1t%WtP+Scb5;_y)~xJF!6EWm{waO=JS`^tGk~zx3_-<mP`p@N;?$39nvtD!{H{@z@QO}`y-%HPY6O;cc)=S&Y`I4T^b_`Rp9AZCf3wCnPN>I!o)$9uJy6|u)EUp$7wj*<BdGow3z%lFx1)Qoy<p|xC)|vTVH=~X4N7@pT0M=5@Ky{IYM|7xZ2L+Dlp;E=y<Pzt>+4pojcgkS*KmIx-T4`LcA=o5s0CJj#tH*roMUx##F8qhE_~2!MmHA>xZ-$Xj*OmxSgPH=i~d6vaPrG=W%b1ucf0?GY1((Vi0F#KGe~zARD}gvtqC1-9(6>9E>Gj2<#t_sWjS9C`}RbL$vsqdS6R0R2Mx=_g(tfQEl`yMam@fw)s@XJ2z2&gx5p>o6f_rUK0_@IN?kkCKhz>0;BWobfcqhep*zv0UKuYNgot&>a+mzJawkV_yRu3%)C986?JZA%PvY0yTjPnI=8%F#;R?OiIgeL(UrqnGhT%Uh@k9UkZl^Y0bIZAI@8e##h=awDEPX)$%7wqNFg{cR?cL@jNLpv+p`d)dz)tD#Z)f^QeXhtF0y2xePI5tl8kCb9Nz_>NJev#U)p0mupLAbO!a(nmcweVK=>az4d9SnewxH1TU0Q=Wr+{L_FKDNM%iX<$a%i9;D>yqnLV-V1uy_YTf-XXw#)3fVgEdnhl1RsgH7NWWZ_npw(?3g8VJTMo^whIz?c`#HfNjz*cuFf<&Xsfs&hU4;b$rRkB?MZQo*Y!k3dfNeuiA|F-Y#h_CfktfN!z4VF~0+35Bgq0DoqA9)<J`aJ%*yY=d(Bc30LE4USBIVAK(3j>;ctLLr=(%I#OoQmW>87_I@hE_W0BXz>30@%qo(l^6L*?Jx68zaEf$yQROsZy`bl60$yx*R0(s28+&y6*zd?<Me@-?N%b#@`AXHm7imVp@h`aW6Dv1BYSVAPmSRQC~2*E4vkb2dWZ`%JxX%YshAsOjpZr_Ok1}NNnnX<5g(p?&Ka2N7By<maU>1Y%CEIXX))&7(q`Eu!}m&Tq30A_4`&AN)V>P;R&!1y$G7mInsA=EMxk#us&!-=(Ao1mTD?7N#e)m0b*#n?51bYXt)vr4oWjA&tbIWX>C9bm&r|Mj7B%3>cOUz7*!CwjIm~-n)yo@$Nd4&cNU3K10l|Qu4W)C-uCCyRucI@C{7%!TI);M|43Eq|Cj?zDwyC@8sl&?b7%@jO&z8(>ewayw?M&I1wUP&W(lD7P->zcluw<OJy8=W}&|3b^2wUT|1X2qnsE2wGy*R|K#dRjt^oltg1qJY-{;(F=ZSe`(RmWYHQ%2DC*VI9b2oYeNHQq632y#mkfsxkst+4r$7fbPb65u479CbnzIC%h4f(94t&R7$hKeyMH)`k`;ZMSxEfp{j+#aRX_Or5c!GLEPUNLL|V1LRi}!eNR9T@X=w3co{{%p-m1oW>_;RsH0734;hsv6s-S*TH(-p2xu`WbeQ11A~evFD8KAwv7hRh2XX4^P+C(Hm?#(ms`mqB9&0m#eJXTaWP8^nExu<p$4y)Tv3lJPW`9~vklN7Y4nK)?$AR9%3<SInbce42Na@qtz*n!Z`xW0PSqxpJGaxfh+)@bByADDHfwdXFjEZot>N`1*{Y1@i^MX?Y6}2$eZI9Yak72zP{T|^(A>qFdjkYvTy3&00K%~U3WnctTQA#SMO=YGNh_rRa!3$k0L4a8nvi=YEF^GrZQ{mA^TM#adehrAg@W5LJO*;C9$9bGI*sF2*TG|x&b4RJGzLvtNpn~UbC1NLX$RWgVsfR>Lw0fjKY$Jc7aHvD<KgTH$%xV%fFHH->CASA;{uYG<sLg5Pq%7mWPo&kZjok@Z9!2%<I-`|o{_?6u^Fk&jEx^&5a}LaZH`l|^EK4hp)S-|t@5EY(&a#)oit%k)5^g+@ses{^nv1CIbnf=FwdL3(DF5PZ#nhHL(g##Wdep}IhUM<QL}CoG6{mK`_fSjLD4(NWF9_Gy)roaED2b18GTu){&jG+>epqs_G|ezjBk_;Jj*dG72}|VGTJ6n)FdC#*vOc%B`d@O;DPKqkd3QGnP!)EPX<;r2pfSB-@hWlqvy0}(*aYCry+oDA^$xUt?XJglmtQ3W?tfwVb(F-#34{7mrhtX-X@Vf;-;~&EON2aI5$J;paw+oMVnz(kQu`kSENjqkdK-Boc2IbSP34&rLd}Q1aX&HtBD3#j*O7rS@EpaHP)7Iw5C|+^1Ldm>CTeTno0{Z*z3e0-Eq}74e4V;Zr@>KrKC@%&6WFSXj)UzJL5z&5!ITAAcYRyMuFO==x^2Y;wi~1PT4jax7lMf{n8R6ftTHv)An2@IL+~a7{GE+1Ee7mTr)xSjFdVnMg(6Jg^4$2f=Yn^L!2@Y-?!uj+W9Zii~1Fodqtes0@9HX5C-LBojhJx)Rkn)5^9}IIj($fBq}Kt*3+zvatalj_%!i`(I-+bua9YOm0QlWA9ORCY<h8I*yd<C51m;(jL6mF^a}Z(2Em0%2v3|H(icb;>GFv%{Ui=qp1Or#;<VWkS~Jx!5(2Gk$Q5@)Tn1}H&7M-KPNTU2yKas#3kP-;MI{Ill6NV&eiTkj`*wL>I>9*Jl`WZ2-cxAqX)j4Z^^j4|!lYZDfyfF|s2G;cgekPIRm{++QNU-GV<RZ<Nog#wpgO#MaAwRqHKd6|>jbr))zs`BLEGp5p7wl+nHreWibXAc2xQ>NI2!HI2szYJUO^0J6aa!&T%gK8aCISib==j23uLp&)QeiY5?rlCY#?>VDwENPDFGXW`>E_|GY6e1?9t$QI$~<ddqvDkma1vV9EAEFhlp$LBQVK9>Qia>a&{_^94^!xS1RG;kwdw*m*H5d(h8dLr$j!b;1qEsff+9$8*VkO+>!#<m6oi=qTYQq<0YQ9maSEi{insWIK0S+3ydezCBYllkjPd$A;%a^(~6IwqX8K0{IswM9t*`eqb@me%9;<%4JpX-iN2xJo*tDz?);4*%NGj*yoBKab8gjT$lLy;)e>e7@o`Jye)oLeP95BR4bPVq5$CB0vXL;>*Tv8+kc@Af^{%R*%xVy#;3Is)J1=<MUkRa$*<bWc_3{ke`UV8IpazaUS~4|(vhs_ee0?OlXw;f)<RizrMfrB$SaI>Q`=0y@%~mayCDTmQTtlNa8H!S2uo@2Mp%O@MeSXn%HW>0=RW#VAvM;H;TP*<6Q|1{MU0@SZ`f_D@84$_+)ixMgW4i)m@NkA{aD7OXNxFw)VuYtQPvjFQ_rfZOL9GckiGu!0HUCT$>;NsO^;k-RXF>QlA0RLL!Q+rxc6_|sGnimCD5!TX2ldu%Oz-UZe4Dt4aOm7T5xW=0@YqS8c|3!XsuBH{D9@Xf<8og^rSC#^bo!;mX*Oz!)QP>V*(%VgVLvN6e!d0n5r09f_!tghsvTWa)N(}SH&C1Y+=woE;!Ye-x(H>1F7GQ9jljXBPw8~IrkVPV-z`lm(=msUyIAQy;YHTPxmJdV7*h(%Hb<mQ=xP=edZf{LsrZ@bYegn|Nh8h5DP$B>8qeh<h$K3Mdt!u0-C}e2z8x_E7xzY7oO;L-$vWwX%mxPQW>LyTRTE3-?jS_?9<{)=wWKuLEaBsGbYr8gDUBf99=Td!9Ofqq9WZ)wiF_+P^93|C;l*c@GO{NtLxF^>a7HfCQshYqt5U}<O42HD4&HzKXOeOJUEXA(S$3|U3x)1AZ<=@eRLaq32o<X-D0~y-hon-~z4Luql^5AJWH-~|g`gxqm1UicUakyTLW@iw1^rn@`|$ZIasm!t`QXGY)`1td1iH41x4|A<zElc9jVV8jG{8#|c9k6~&;>GhLl^X`5Mj&Yf{H9;MVX_QSRiK-6hX2vbOYqtiG}~VgD%x<0YRF-ms*h4Y@l@JaZ`s_52EH>)5K0*fdBw|;rDTK#3E*BXi^GDrC4sj{+&uRpUWA|Oo8~koM$bBs}tV0aYvEY<2VRiGf@P-vX(SeGLAb{^cN(pxX@l8;s3l^rM*;QZ8)^ah<5~jG?_tb-dK)?E68BSua_k?0Ln~Ci1?d93i$km{5!=_GguEK8v-7cq$Eiq$u~bTodkCsrpP1?H%vmKPx`iyLOxK=aDWQiq+<3Qul|7u=+BsD9n&zl^>q}E#(}d)D!f-}(f6D^Qp$C7=O%GUhDkqJ$~6e`4;RTR=$<_`XLM$ERdrv0;49S<SSEKxgv_WOkjOKt@wMf>k@*dF6FizgV5a2NYoPG@exNcOQqjqf5uMbaO9>6i8^4o$bAi`AIATtHDm6njr`yX><_jZ8&KzWF#wNkeIFOsd0jNu7PL!N-?DOzcv<ZCGwYJ#=NT8cF6`#pGHKP*Xxue*xrqORC$p=x1x=t4XYy_H4qzNL57@3wPCGUx)K~eyHgKJy^)4<WEQjr#Az%N409%H&hpe50eY&%G6TojL7F}_TAkA^`NpCRHts%axk2RgdY$ULQ$3o#dC|C5KcFqChhuGfTMPmy7CYVg`EJY=J+-t2H`<MOkmDt9x;G*`e?CB`?7sg|r~o>nDAtpYPE)=Mxhy3-?JUE4~LfL`&Y$zD3BCpq0%mn^O6ABSA=%+d@`29WiuH_)gUZ@xy!7+<fTmgIydvjF}*uQo()9Zz2lP05I&r>|Up!mr6VLT=m88WA}x2HA+wDaNVQX<}xFb|Tv^X=%nHB&gNc5S8N;Ewx&tSTFZMb^j7)s7vUFqIP`TAdf|)O8KjRRRTc<oLV&~8QhsqR6H6P_LWmEc)69$XQNhuKkgoZ#gz=#em^pml?A!-7`hmiXVjUr7jMge3sIzYU~4cbx${>Bl9mSIY8S4gIXWsMA(U(%U2a6%Sz4J4iI*`rIh@B!Qj*jplDy_@o1_OVxkK1rt9<G-5*m?xr1F|Q^K@o_KYV38Q}fG!k0j1HqA%jzuXaVr2hwH*X)lmLsV}LTWX=J^)Dp3#pwmULW6xd`O>4irUIq@8Xz3_KEvG=naGq9%Zs@ricOnRPcGSWdj#f=>sB}`f4&yr<hw{20YW)|h{kCf-f?8yjmX4>Xr)ED(ODh2o%ZWNF{Z(!JB7E5rR+N({@qo)KOsUz?5<4_}Mi2|}{ceSFrJ|qV2q&yLOJPysTQOFHaSw2vkd5eO7XZ=}A>v~X#<&n3eRJPe_Cti~D3hu(;urT$VF{72q*XJCsek@Dam$D3IoN8I4Aq2Jn%*9Iu1-)!y|XoU)@7=O1@ctnPjp63YE>FKK*^Q_>-|X5M;(4Tvs6fH`MmH%Tff3nhYAK0vmw(=7plOYG8u};7O^3)Q(J!o$O*T<A<G63a^y&XqHxF1CXpW$XB_6Vq6(`KcB>nZ0-7`QE9%QcVl^W>H!5TB0J}Oc*Wb`w!iY)r{KZ{ge2!rP-K-1B%11-4(mOiM7XuwAh%7S$$W&1_T*|=}YrMonSE$uOeU4fAwO#S0{5utN8(SV0m4eNxR7h7jDr`|isYFQ+Fzpz7>enM8*b`U;0nO_0U+JV1<Fi{IsC5~u$y$`qQYuVI2_-Fz6D(EaA&RV;+=gr~Kco}ijz?PjC5AiPIs=qe*MfP6En{f`c#A3UqLj^m(=^FB%a)|Tv+yQ9$(e3Z=Nwv;a#d}84NpXc^Hq(`l!Tt(`mI-r7DdFmHIKm2g^9Epn7RKdJtdM1Q)PG)xGIb0lo)8tvkzTbLW0Rk85!6iDpHec!fB;MGYMsO%4pTBxI|VaN*1VT=^fIzSRledD%6}7l!_?Xj08A#?sE#KNMHyneZ~kvaCZq&$9#z$pZ0^Y<DRh&@Q+_BYl0vr7|L@O%TihT&s{Go^~}X+(Glup)j=I<d3987RuaKT*wILpA0i}GP|mE#EE$qYd5w%(fzQ_SoZRDc*SNc9!ot+FI9UQ%P}DBw_E3x1&03%5a_3pDimqs2!sp7XfkgnuNTV?)mI2EqOT=Tdj4eY4Pne&xAw}RwAqmkI%{h8v7ELlSBr_<R7w*GFpF0x$&V~Lk+6oqFZo^C1D;BfA<#d@PadGm+N4+_`QCcKfT%B63>(Jsp%;jwDfjG;UpVx&Xr*mi4-j;M$sLRR169-g&zz12!ySj@#(7dAui7;fvDOr+@UEk`}XawLO(n>Z`+YYbo5Jn%fKNW0@vlWflNpSqy$yM6PLrTmWi5GGX^O!n`19)ayS0q*Q!6mZvKENd>bu5iWJ<87Y%~CHqHa%BYXRSulIoD`PO{XKnW^06tttqo;Js>SEx{MbK!@+_L16bMg&uJ#zS>E@t+@v14Zn(`@JlX)@?&2si(IqenGi8ZjQpGC^wxW?j1z=OeJWFCiwK^}LKr@Md7lB8Of3170P{JbSgHd(fjU>0Gnf=Tuy^DkUMUs(XN*2oyab5xAO2Bvon*Sp#VbsE0UOhQlnB`ZZBe7L%o(^G9cGHvGsn@~a`lbwDO}GIbiAF4krI*Xo>TwZY+RzcsJUzYepQaQgf!4Mh&kT|fYM8m2<DQ2&wS9|fT$08#o;`)*5^EGmuyvo3u~o+^1w|SEOIURmwdM8g_`JRGLkC*I)uUr5P>e2^EN-VrIt3Y&GT%}~yyj1np%ulrmpOW|eW<urvrJ=J1e^&{5LV}7w+DB(DlK(4FKy3wX_AhfL>KMD#<R($X`o>JnIznu3i|_0vPv8qTL1|_F{`0f?m_0<Zl%*2lbcu{D*BN3cGbPi7em3Z#RW~V3nyfG7M#(m*Q~o3=+P9Th$2Ad;*Czi<EH$boPl>odwuTJnQx^zq+~t4f>$-;uo<m^vQi!%S7XvWL%DiG!&^__OSmk81*+6~G71*5@MXgAsFC#7JzOb({!n`d=h@^_(^o{S#+_n#B`<j;&5=xgjPFjBA+cDMf|fFQEYCFoLuiy!Q|6DX%?$2IZZ4LnGfvb*Uyc-%X(Z~V7Thw6DO0kdXR)^LEiYE0Kb@s$ade2HF2|Wy(ic`FP7~G2<RFcyyew@wu(m|~FxL4_;it-G!@{ixirANoQ6o}Q36xNst4Z6+oK(^*S{O9&UI-!$R_sy9I%NC7Fd2x7vl5~FkDJk&SIa(y^mdUpXa|pXDjIFaI%+8NNU%Dg7$T3v9u8KDnuO&6JEoaR{wrc`VnirYD;=SRrS4p4F2nUOiymYuHPmhw>Wm(BLrWrdk|JBI%@);vsFzZ_cnUajX%O?43kqGnbQQ24q?F=$y_DjMt)N)K7}fYM;7A?0aAIfbYdYq#w%5qYi=COT(ut~9K&0&Rk%_F-*%D<_%;97;-*l`$?PHv2q={WSa$lIkl{lY@M9v5hypqGg6$e8JlG@3@wPN7d1<g(}k}R1SGT|yBBq|X(K>L}Ku1npUlzA8g3Z%rsG=;jo?^vY)t>7EA)dOfnM@ZHsID{_ppiNu@9amXPT__#4VhN1<Pa1ni-i%QmNH-#*5cvq7iqC+FBcAsyAvzy9ZBB?lr6f7U$Bq}2S8kKwFQBYo1eO*`2`)O5*E#mlP{F8%U9>c%U~Ga5D5@1fREQvUiS&t-R>?aeEIEy8h8n0)G8x$;pPuuftWxo$Vl+yLL&qDxdK!JPX(P(e1;DpoWR*a#w0oKKCAwS!;G(2^1<F1$pG%S!t0aDDd4eK|Cb@Q>E+w$e=(>|-#@xuNo<A<rw-V}O2bVA>v_|KX==QL6m*GVsIljQ0ViUJ?%CU=^L@LHPKeAXOSNBF5U#^hAxG>p3i`A`zc7vcL*Ic34o^GgRf}^R2e_2^3$TlMhFq13;A)#)ZpHGe|OQ8|m<5IrRq~Gc}1?W?2c1)?sAR7g>!TOWxp`IlYIoi1Ep2Qc@SFY7GO?1;Tc{*y9dqlZ6C4O#&CG8X|m9u%?bj+v3)(zli;eI1HY>jLj&f(I^PoSJDFaj;oN67re)H8?u9zeQ5j5#c_EP;MLfAdY3Rv`642=Y5QVEDDpA18Kl-NC?#(LuH0Oq3wv!E%#}u!zN@gf7@X!-@ic8VIi*Cq;p^ECNIW*9<m`J0&5|6~R|3%P0|}-I6Bu!9JSk1o%uX@cp=?qq?vI)V$t2bJpdor+pctRwkywd%El>f!JI5ut*28>mUla++|;?Ws02`KM-po@&LwhvM_rYQevG&3#jPGzSOK}<w&mSg|{b^W`OD#X)e2;^KVlZ|FSQ`&Da_!p{2EgWuQu6k}P|0CL*Uz(K0I2P=J;$O7Z_zZ4TrRWi{lb)Ejo7MJYimV}(gX09YaCph{*#!;)zA73Uwh@JRDbtlWo;6CqAd52FOBFzS;q5@tT0=7~vpr+lzw=}#oiLf8O#eKd@K2t`P|M)tg#)us<)M0TA+rnQE4k037=97%Y23xO1sItFR>X11XaZWJ>&<*4I=!1=z`IJ@UWz?#xe3=k&EWol81BqWe;9x+v~61`J$DK+(a7T`^Y-Ij+!iy>&VD$W^~s#<6k{YqW&L~v9y_Lzqf<9G!+<#G_}bFQn)FU~MP^uyF?j9|7GTfec8%%+fIv@(rGwWo@zR6_Kq*EN)HRZi(YxJ8$eHJ~W1C$$!HvFag|FkqMYAdJQ>)oO{1E1#E1dZ?CiUuGTH{)q#Yls*C7a*;SY%e{p|QY2Sn?n{g_O9l;GCG3>L1uz)MCRVB#VTCBRAd??zyPE)PrpL6hOhHw^Ll8em)wB4CZidm=VM7rex!M<=jacd97{VPH5jGdhX1l(V*Q+@ccZxW<x(v;1(2D_{1zrYaC2WgEdLgE1(76%IXcEYYqBo;h;$ZtWIaX|h+1+Lyp&hc(vpQzENOrg-R8k`7<&n08CLWX(_n<88S}tr^*PUSn<RoMA@458Qh|7Z(^rW~G7w3;VuN3GrJ3+P&5g)tLYP1leWW@Fu!QwgKb+>}*i%2USkrNkhyP%TxIM!<m@)CYeuUF&{l$oKP!zK`B@I7@_;9FD!65RE*6aCTZ^>qk|$EbZx{Jd1CPcX1c?Ib~IDhk0C0+AyYCf}l#vw*K$buoqVaxax_ZF-?;NrRnIQO+@wQE0OEXd;iadY3HZSgKT~8-hYzC?YEEm7~)mSZWfZMzV2Y)S6Bsoo+WnrBJ<^a~Z@Xr3>~LPDu*g$R)>|R2XZDnaXbF?{x|1SIQlMx<?R6BENU)0*XYAxPsCF5hMOtd=Of#+dfZgn(_gRXl+i1w`{Kd%4J}mtXWnKt=Crdw`vZX(7?|{;ND(RJ(!SO%hOz3=P{9DCE9<c_v$DBNdQMFsGnAI%uBW8o{4EDZbU>GfP^F!Q0HD#QGWK)zV0S`HB$B?x5jB5M=>Tw4Y-~qmODujBi0fm-A4;<Z$2riC81U3QRtUWR4FL{YNlBz)55EdaBU>lnU@Sq3RnY)`hqqsFtY^24_HB7UuiW^nm%iJyxaB7Uregc+*xI-LK(NUBdVwtR*#3!I{1kY5E&2Sm1FyAKve9Kd%C`g!I<HF-5u@w(#((FC?8l5D_rM?k{4Ukw6q+U_t$>--s+5Rb^m|=P4oZ')).decode('utf-8'))
_LEGACY_ACTIONS_6C12S_4Q_FIRST_YARN = json.loads(zlib.decompress(base64.b85decode('c-rk<%Wfn|a{L#bd0;(QBz5C-*J>Ke88%3^3ade3Fo0GNAgm4}-Gu#j^^*0-%CImu^N3`#N4yn^#msnzyScgfFaLY?@4x;2x4-^=_D{c@{qW_}-N#=)-#$Kld03xq&(HqjxBvRL|Ni=yuOI*R+wcGR*Z=wY`IoaFKRy3d`|!h;zx;ap^QWI~@6OK8KHP84&gaF~k3X*0p9g<<T(3WV{d)7``u6GU{A%>|PwTt;pU=)`ho66bxc~U&!_)CUR@?30&xalR{OQA=zkEKvX*THFFK3(e<I{6nf4+Zs`tkYG;j7Vy(}8$g-`ySGx){H8|G2@cKtqPFJ$@Qb1!}<Pb=BE}Jv_AJc}`|0eck<vyzBGb?T2-3JW+r4{{Y@LYBzc7?q7!ES+wK%yPuDX;iRv-nX3FO9O3ot`2EM_ar?A>7%!sncc-fdF5UTf5k202884!8asKHaJLBY=QSaDPmV<LTz@t$*_V2^(ZfWj+^s+MtUAN})I9%mR_oFcURXAN>|DnkNJE2&?<So0g2V*uEj$+2j-{>>88+ST%C(j-4yyFm-(^OfPGvROpo1uEN^0Vcn3);w{LnofReM|MRl)s7R5e(t(gaLCD&6_@mhj$!4d_8*~(Fbqfj^p0);N36jr1yP3o$xLl*#Ga~O<kWGe)tBD9o;I6iZvM=rp5)*=c(hf)!DwU-h#0`LVjA95q(<l;r{M!{o(1?Kdm30KHYu#*V8kh)8M6FVl0vLJ0_Zg{jEJ{PjwF+9FftFD_8mD*02EI^!hjEcihKi-n$L$zebw`n0JNwI55J&!p-;@z!-sh0{3dSv@J84_hH!EsE^?Q0>|DkNSUhwKSd8@V}U+}4`d#JXg@aiqxB{y9jN-CO17`Efv9gD&p+{W+FV}+cnTi}y=B9B0LK0Ck)<&hZ~hWEA+}}QKI?IzsY-COS2nEQpVt3r^1Tmis3iulXH7-{0+K~jgI#QGR~$ogDz|fJ9VD*7$Pj3R>ZFUIi-CY}#_FY!yc-#~emt(*Mg_dgc{DW^z*}nbAKnO>4UsZW$nbEhEq*iwr~#a20e}SOq9fAffQGBI>&ZXH(*8Ke+52PPA8TS#b?e2B)q`MqB`P0ST9=tKGvkY!;7HQtGr*9x=wW1cWegM#QgYf)LgKAnD7(`uWAo$f!@txz)(RL6x}&@LVh9=y)uAuRAsUWF3qPP7oHBrTU;;FuAbijd9ea7J>C6Co<S;11k&3Yl0FIn2yW<+&56UrIDG&PbiRe-pzHe+_S<&G=!Ghjg;0>AZaQWbp<MeJIyg#-T;kk5dq|4_$e?sHC)<K`D5w$aw9-kg=H$SW&9{vJ=bSZAcF0pFEmA6|^NE~B2ZAq8l(ndd$eIrVbpM~RQ7=~l`svS}?q8Kdbw3*6i8rmB}h|0r^crdGJeH=a<F6sDj8VtL?V+Y$1b5T1+9-I7)@dzYWL9O4`*DuY?+IZ;GOG7ge&+^_P{4;?%?L01n^G(K%dyg}HtEkn=wrLtHmBlu3d{WHd<W*lc;=}!uXOf`vRq>Ch`yJscnR|r+5QAHAbANyLoTdVesNElTGxYU<{3t{MkG{ASu1nL0&f%mMnKz7_(1|TF9@N?eARDp!$&rUV2b}>!2W0*9zU6zzz)0dt=CYMgp{4+;?s&8@jmo%h2wX{EYVj!zKduvDMbJcmVje$bz&Zr_4fsdEVr<?D#t4*ij!v}k*^t=_Y^>2Ib7a8zQzE<L*mI6Y1zd}fl{%F%w94e5+Cej5MJ;jIY#AF@Fh|t3xTc{LMK;rMxfGP0LvOsp0A+Z(k+B@FvYZ(Z0t(H^%GZ&(#$f{W1OeW8oc4R3&WM)NbxAH_L{Ayzyn2=*$^)kBou~E6n8GZcm_sxQwx={ERM^qF%a3t9i#=spr{#OgV?&&awotoeZsXRmdtNsdtJiI%A;zr?Heq=Lkb57rX!N&ahAXoP!Vf725%jm(sbq)A9A~=e8+By5hlifj7;afA!y%cN^x=tyS)+3}cInQG7p*r4N96=10*c3{7Cra2h8%&#>C2g5iS<s<icmkGA<mr4Z&5QS>n=(=Pw$2}BQr;uX2|<1Zz%XP%L7RyPf+9N@W&R4UXDd~*vCWMx8?}!e=CGtEi;?bM6ubhe>i3mrGn-jq6iMf!#wWq>z_W|{du>*YF<+L%Q%&;1q|P9-<S8z=JBpvkX?C&A%Y_Q5=}5zSvH2iJsy2t2|pLCL$I#}?HF%&cu^%GvvW$dCvYwwxtl|)r@%x?il^tV<;L<blf#1~riGpdIle+P5$v?k%`C|o1C6l23Z<>Y$7ma_4(1&gq-=Kqg|qSj$uMe3ZUrud2&2?pf|w}lfzGAP%)C9vIn2QwV9dZgCO%}7yBnOcE{!AGpiTu(;ucDK;4q+VQ2LP*jG#BG<uP1ok~E$%V$hhdFSR0aioru%h(KYkN6j!4zbsx5a@#C_UHM={=6ZYD-;6W0Qh4CG5TWmRFKhQX`JJW*HHAwKERe_}C+u4<s;N8Zah$F&XsG?{LJ6t^026<(p((qyR<2)5)+BT4%T>(17d^(S6MA%A;};It60aq26#`F(NDj3{j|pjQS;Zj)qSf%mJRO8IyHJT;VJ+Sgx1ilN+~|^xiM6;zr&;+2kDpc^S>oGxh6pf?8h{Fo1x1k?$*s*~JDa{V!$*<q3E0PEB_-Wz0K6CWSw#wF3~Uesy8&G(7cO&QB`cNLt1RM;K-8H*-(|w%MtrEzex-0#&ZJK^Od3y?dY)-OFE>DmH@-%*@+8l0j$F$y0#j~k-!8XF-a@P1=wLO5`@i7^eaq-U+J}y*Io~eiPKYry_sVkAMB1JVL0Hjuxs}Wa%*3Uxwr%pnN!JTlW0O!u!8&OZjP$(8HUcQ%yRwB4ME=l2I!agLS24J%nuF9_N2kPVGzu$CnJdAqevUKNMH1t-QzV5+p<LYR+QJMm;G3<!or6qPw#HB-n5?!6Ag|B27H@_f0u2P)ENt!U!of$#!NQgW$UZrK1;hBbt=DC&qh2iHYHLt>DMrFqFzc=w;y^uH8Mp<R7dCldUN~BjZ8}LBLE?04A(nd}&<$%U+RN+Yzq7p~*(kh~G)LBtK$XGlxKD9O%9+q#c8&qBKpPa4LQA@snaay;CUcHrtclb^I39qyEq8U*n6y=biO5!iU~;wOV$1_svt3lBgP~PoC&t0SuG}h+`6@{7089+E7%m2d{s&7=uH&PjH~|9qv=?<kL(i)-6OF&isn`$0#qe-ElCx>m-xr~iPU+Y4MK<MugEBf6b2=jPspuDR$zaR%o}7qrWcgEy`V{y_OXf1DdTYU9ED|c`f)7V3qfR8VESeKQyyuqo=&+}HeQ0IbsY2uovIx782vO4o#wiGtMH~wf2K>m%6@I<VphO|E=O&+q<nks82Jo*KKU<}{tQ({zOUh9xjYA3l64sDhD=}7pspiF=f87NkS!|5lR#!d>)=6Dd-aAiNj&UgdZmV-roF^i{H|sYIocnSM_zFq1JUj7~IxtY=qygqW(}c%z8;P#K%z$Tt(O(OIS$zg3x~()Av!$gP6EwV?v}32K4UtBYbW>54gD6?UTrKRzOAEzmWi)AP^d(`OP5rK`k%U6L$rufe-(l6utRdGb3x3ojBq~HO>3|6a-%KLv^g$4dw(*>2?B=qHkWPT<^n`6(fQKdfPX*urBqs<}7Fg79POh7!T@S~$o;;H$;4rW|ZamDEsY%5NNDFn_qE7m!M4fbX%%D0<Mpwk8^huiNGZeBgWLcv5=~Me#Pfyc$D<~|WS)m%8ie#pNQd|j=S4BqNNLMI#81=?ELnMLNl&FY^1~3W0lCh9OYDgqrVw=?hiQyE^T_qU}B=YjMy7<mgN)LnD6q1KXO>$ggUhEJ36`^5@nom-Nk2z4>|Dj^I3HlzGP|eR{@*a|8d=kBp_-9gFSrhimx_#iVRp+=IP?fEj_ECvFs6_24Ju9A-4z)Hpslr{X+A>%=^h0;clR>VdA^s^UEd~ah41T2mMPznto&>AYMInBwGN$s`qUJ7|X&o<V*4Gsn;Ibfl%)Xg+Mh`6D)zmCYt69YW1`8Y62JtF!X&a@b-%JJo)?)!=h<X5-A~G<0D3o+#>;W^^!^4Ey%Q`7DkwFm%Xtr!xVP;_hX>$lVIq|*3R+A(RNkemu<}+HEK_o-WTMC&kjnte7m(jHPz~!GTa#m(_kOEERI+k)91QxrW)+4PB>d$i{cJHH(QedKZkBCtyB2Fylf`Uu+TosD_8}uz8gGC3ORQB@H^jM=nReC<fY6U$nHI7!aS_=pbn@4iU<!Y|k)28A%#)uI;Wj=w}B^`cCae+)#11))txRaW{$D~)aBZg>S@mw}ZBep)SwqHrn9I;jnt-U57Dj7IlId7vCDAeJw$CH5cd_N0&rJji*N*U7~Rjo8_3;#4jj7juhRm&**9w33x)47=n5eWQH!)LI3FCoy6Zy3`F_FQ!t>@brl5=EuTDHAj2I%-4s^ViSQZ}XDH5t1Y8H;px9!l?P-4_(wchv(lilRPE5aV-kn<)q2}d8$yIG-F@^4T^~jr^qQtD7l=fx@LNRYyKNiUeUNIhD%1rox43LUy!CiXp*LhlN@y<a&;*UIJ4kt7pscgHB!noF$HcJrxBm@N{|Q&-aufL5;sa0znax+@S@seHTYn+MuH!nM#D4Lo{ub<y0Swg@e7?d)7jBkmdY8+KZNhInw%P~#z)byBuk2?Q`#l-Og1DWy%U!ct;Ro<&w&bFDj=O;M(Y|sBCA;Au``Do;~VpBf=G=j<M|Q;VISm02D@fSTLNRUM9BvyXlU27>zV6SMd!3mK4m*zUv@02oi4_~=-Sl1Vd89IEQm!SQXyBu^)3nhl9#T@V=4ffxZfEWuT1m+3tW$fOHOJ+&X8rH5*{qq*bwt8W%)m))nMg|#UZr1;QnCWY;ztey1u2Ncf@zIge0#86G@l*;6?>Sxd@XbUNo0h%uS_FNb0C+K@L%dPl+B1us(0H1`nV<S_-9|G8mYWrGY8%IBr%Y5%{$n<ibr?KQ$atc(t8Rl8`{y+)A>)DsI>^lR~9o%1#%LFfn3YeO1qCT_l+a8W&3}w?yk|wf1msZBJI3g{ljb5)4ILzGZ2)D>&BQ@a#0rhA381%>Fw>x2SgG3;XYCa#$;bT1fIgq&80wI_{qOpCP~5<NzbYYn4RL5(4_B@xKb^Lv}+AErB#$U<3v+IpUXo^&`>8Fb=r(Xtmi!zPwtERt(o?Xcpj*CcJ@K+(;l%vY`r++JX89@}0TQpXJ36J#JJcF;+vVSV`ex2Qvi_0g8n<c_PL7&W8F}`frImu~cj)Ko5f`c(rgIgrY6$GcZRZ5s)`xZo%nxWDtxO(q>e83ZR@e$gRz=5PegyC*o17G>tnfDy}nEtY9Y%KF~3u`2v3YM}#!2;Z*7L$bVU=z8;}Hw0r_Xoj@d|9FPdt3Nk+okJ>>30&sAxD{l6|-1@o0L*I8<xXFO)as8chJ-T$m@`_<CG8U)&7F3Un^qERuitQB7L*A@yyaA=J!N5#LKaRP~9pDJqv-X7fZtiwry@qb%DNSNm@(CsA5-5Z)BC4g3uAKx}>JprW?S*K)4xOZmHL|J&glM4iwWwBln%tpOLu5x(1PO4_nwDCafF5%jiFN6uxu!~4G|U_1VZpOTt4G<$gVU>>ia~Uqev@Mnm&c$~UAKbvaZa)xXkKg$R<=r2P>G&ieKAT<W7v+K5eAofjo{7QU405xj+7RtIKY4fn=~Sh|BW;Lt#Zgw(4PVjwtH7}4J#~51gP?FHPly%dB^VAQiOe&@e;3hz6YcM$wL8U(;b}$S}2P0+Y-bHfkxXZ_K14Me#ItdF!5&X*XJNH2!GEkbS&N*C0qLC)eD6$R28^TXqD%Z<|Ioi1F8jDm6f9-N~%A+d=>YkUCLmH`pjy2h$q!At9a1tyJbhbGWx?bP2L9dQv)3$BY-OgB%@Sns!twQiMqw$x<+S5B*!$D3he_2DTzJ+@d~5PYUxV<*1mQ!dO$%1pnHxsMuz3mS$5&7tri1L&BswxNmXAhJ3lYQc1hLwi&PN@Bh$=Dos;*eI2PC2L|q7Ut<Y#aPk+z&yk3S-*@aO1;v^ljWKBdsfFHJ=&9@m`Rg|El5Gs#p^m7{7#$mOlrN7yR0Pc$tkEh;{CM_sdZcR?el~E=MA@q<=pchpk36Oml*#sN~VK7lYPs}&4xd<z9cR)*2L->il?7(-@w116dc8Pto+BJIKO3b3^cP#CcK_WcQC(oO>c7So9O;q;h<EMXS5~(p{WA!E{t%-dcrkBeAEUFo6ck3#jZlxMEJgQ>Jw)#oa*ZKZwt+lc9hKeDb*X2gbSM<T^3V!->rw@>>>usJJrS>~1wo`rYY*s<%Zr*XX&Lv1F9`p(tI}vOU@wQRI9;!%kIZe$GOc!-J<-sX>x`(31kr3t)njX~7$dq_!tUW+VUAC$0<o~YTJ(t^F*;kqs4v7S|?{S@ybk!X}BL1Q#0Ew})kyu(wWfVhzhi@UmSL!O@$RvjtPfGhLH7N^YVNs|`%N%3>sUkbeOf|{~g#}(VHxg_3wx+sL20~BQ)OkY{9>V>>!6-!*L)YW-&oZS8l&ztt$nZ`j!sSevC{ZvyE-VWs!p~R{O1XM^ZfXe*Y~;zqzi{NNj#==OK^CV1Dl{?=X<IlhE;A=Y@g;0e_khLJSON0|<Q+p~_&N$L#o{(pE!r!>O84`0({>r3WBg#<u*5m9{#cv1%XzX?wR+5w=tvs4Z3+D_rY4E)(5^XE1Sb_3nuvUMRRlIx-)rXK>i}MIrPsQqz;qNdFU!r!H`FpdnqaP22c=cYI91T*6`-$RQR$Mv)pgj_X_Qx<nX^}cV>-;5f=jridl^V9gUIdaQy$P2x%m|!O!5)+PFyy@S{yN~QsW7J)CU=|fGvQhR5RH`ePLBUf@3R-#`?fw5db<duC&O^SWn?;!X<iQSgW3L>i2^nKUmjEUpF*B5}65IdqQ(`H7Hehgnt7v083Ful96-;Pw8=i1ICRv;Fi9*pUqjW5w2Sv54V<dCzY|)E;6M60nM0`70p|8%&*ee04ECvzzBf?SQRU`U<XZ6HP0bh;z27i=a(i}5Y~R6v>Zy&@v5+g)|U)C9t25HcP;yyAco3*rlhlS%HSp6Mc_=<&bLZi>&k_dgIHT!Z5Y%|0X5Z7sZ|9gOCvmBX?@SA)CO4|RQ-yU7!#VEaMuQCP7!Rzjl|!I;777lDr1U4TTReI6qpiC*<=ph*DhdXf`+*SM=g0y7v*kaTlKKD*}R3cBX;7m_1T5o1rqy+HgiHK-Qg<=JvwgyWpzD!BEJ^OQ?qj~6*N+Uc!Zc&A+QhdsB6hE>Nks^cEq)lBxs1|>#}Ba8>Xgm?&JwV|BrL7<jddpNm8C}MnaBa&h^aIHXehpp(=t`#RAmB0W4_PkVCkLS)`@C0YVcXE*DBy;LE8#Yra}jdCbqVxLss<;{S?4Cp$|YOyZ4`^sU11GNQzeo>X^MDPTJy$H6TLR&toVn<NV9mIoDcBCBg1A(Ua+^1fy1ZhF*lizZl$*+t2(MPAx!8)6i-BELB6^*mdpf=8G%opVjY42{E0;4c)v?O0JV6kNuRv{o0hK3)p#H=j|eL94WfCEQw*7Bt+3uIOD!6szh#&#vE-COZ{ytDD8IO(M%fLu&Dx&AKa_%uv|R=}&R^Wr|eDY-S*x038bJlKx2f`D<F_=X97l2bh@K6OnE3w*Uc*CD8j+nTtFdmkTuwjgZoag8a~OS=31iJ=EO@7OD#ZQaWLknBzBJT13aqs-GHo3Zi2Pp@)8_$U>q}7rRR}he=&VRv~h*g6n>uk@sH5TE=T2A@3N}PJ|~E(?G0Y=!{{&4%1p%by61_9z9}WALSPqVC99A<pLr8fHoy1EhqesD|hv9Y7yvA4T+-(J$p|ph2O7)9ln1-#Z(|ZZO!E?c~f8az{CAhx+WWjjC0;E!PdC2P%L3Cn^<k|-LB8OF*QY`SSW2MxK22q0k&D?Kqa->8YKEO%qgC1dhNCqnQQ?qOaHRm%WMc@K&yTnWi`S8RI|vB02gKq<5_f9L@6<>hO;*SrRec8KO{+|v1<c3Jz>V3fNtM;5y%oioD^S+NYoo4S^hOd$-??i2JjS?xnl$&F`la7ZeH#wC(K!*U{pq?5}Ht!(`GUboiKsn2v}5qJGRUhE%U8qFn~~<HPTn*JTDjYG6w`I$_#PBMw6<UcgJT?pxUy;ztD?ns)Q^r86uwRi#GgG%TH7ewKf>FYQ~D@P6E%2FymCoh86%})wanMowifb<0@PMMD(3jRL}4qS9}HR@`5fhT5kc-Cn%uJ(h$_iy|LzY-X@5~xdPEz4(m3xxu%_Z7NjE3Z1dW-HP7Z+=`u30mnqFSy4B9Z6lp=xWh%-Z^I6y-Q+ACCWU32t(cO$H?M4w1XRDFG@O>tV#cANnF}*BgIM8%oo02%QW=|-TVrGT&Av&yZED_&+OV)UM`fhZYuj(@0tQ*$rtnFr`t_?|$l>~gM%bu!UrloG`YW*qihv&c0pb-yEF><a?Mz}F=&}=5ZUXMJe!YZkEv`)E>;LfK;aBDkM$2P08IeSZ7NDv}?6B2to0KYcS=xPre@i7wu6yYVK62p9(t^FD~Lut%22z&}Fu*yZ>CQ8E^S%5OTQm%Td2{PChT)8NtzD4t@uaGvls}av-mmB4V3Ca9%;fKzbnl23xQMQ3|rPsOOt9^3VmL<k=J&Bk#LN(B=5^MGrC0+x;7Gs4>8^7>ynw67{$S-uE2rZhQ*5!CzK&Ll3V1U<iF9{<w-B&zzy*kf*yhc{8mQ!CSyQliqYkPxYO%Ixkr$;@F@)I7YllA@>dtIAA319C6>Fi=1soT<9$6~d|@az(})xDutk(Z3CG1Lp_R@36mD>94@_|((V5DFX)LpwDmE#cj&i;PLnQo^+oQ*nZPGB#`22!5qetqi)l{Z{6EnXblK&Jqisf}N<&Wd>_rY8y0Mr30^_OrG<~en_DPL7Ll{-dP6>HN%YI1*_6EZ5FRic0D=i6~Dd%RC@6Sq0(38yEYWzb)@gpkf<TbWysYW?krSv_i93hYg`S@p~^K^;Y}=<?y3EeShX!7-@;JsB>s3VDSEKhuX@F6sX-Soek_i$US+ov?R29R*(CKNnky76+aME90ykB{rZ%1Cs*G{J1Y5L4QzGQ{sJ*%BO*R7s5+ox%VuRCNo2bzur9LIj(qx>^sC!gpeoc*-D8x!y8_*$tr{tPqbh8BqV-y|vQt?@F^T|RfffuP13}CKln*`#j4G1!sqgtVssIFfMvVB>SSI%*i#!?u$bR)`=h9N_F6dFS=Y(WRf!(2&`^R`|~l9XC=1@c?~|FZ6RALLReWJ$`o`zRo-i!0i;KDOzxWHn%jun-v1#{&=q@bkH%^B#z<BHqcw@a6ND(b{^*JgD;uKr>e9Qfz*)r)L*f<Z>c5$zm$F^Q3<0r5xVceYIB@`F~K$rV{{iOd=RHaZ&veEKT^kYGf(J9bHzZi=3RL+XVxeFslL^b7}ODSzGY^5ydbnqak39GKJD${<E}KCCjrZEx%S)%d_^K>Obg;5>p_p9!PAxa_z)|r$CF-A`lI?XF3SKVTztI#u``mwOM?<k`Tdx8%_<geiCH8UGuM+OmPwuU@jvo=`Bk31r+s#tA&>+rDEmhv&gezf5y`#RLAzN4zM(VlPOhOmCeqs9utJe%LA?in)gLq<Z8%0!#ThM;zX42<e==HI?-_IfKC|$c1tpBTuHQ^T=S^bXz?MG<n!W?T^5^2pu!EWN=q`Q{P<6M@AT!I>7uJNZaZ9CY6<yT;d!O}?aMLKc?VtOF_euYNlx}vC-U(kk57{zDNi&$oyXd&Dry$F`83w3R)1w3repfO2vh!=N-ssBS#7e2hG$CgoO1tdYa@`&-w2|JXf<}3zFsNXvz1;z`j4cgSq9*$49xkPVIc-80_z&w7@BDWY2d81sJvW9E?z(<jP>|Jju($ni)STF6K7x)Y?i}i0%xWP_ep``Bn1+t81Up$;aFT|@<d5ACeC=x@OrEs5R^#^d74%q@tmq8naeh?qF73LF>Jlkoi7`ZA<U4hB3g?n%O2^H(qCRU*#gh;$s5k7)LR22mx`7u1SUm2t+my*#G+r-X`?}{f}h6rfiId!hBvswMV4oqdRZA^2a`Y+4Y8N3MMJdZ;42hOErBbfUD8$+ST})6L43s2a|Q{Q<O(ZaOzo|laXuHkZk2jB?88A%fhXG#L4vUV4LQjYWGv-BDjPs3R+cz0y()>B!XIV%qDVI)-I+ydKkgS9xYv|RxO~v*1A9ygjlu*4psSp`61UnoB8RGEmvUOL{JU!W4xjkrNk9uRJu%B($W;~DoY(RI0O&LC4Re+A@CGX{*Y2j}BsG~?YBuvn6=X$AnbqrywrjJ&fn7A~C1+bsC|S*<Fo0%B*1gvQmgdxyQAlg%vgn{LBWWGeh+q@QRDf1eP3YJ&4G>B_odS$0v?z4}7q-e+mDZq=q_v*-1xiHbH4?iwS5eYn5Vzv>h*GO(BUZu)REE&tO4y6yU&O4Yf84sakB?e?h;dV`=E;*fFh}<-qfI>g(Nu_)s0UODt7zWQLo5Dt_#p5aOQ7K8pV8E^(Mo)1Y!)nV`UcvC4~n<YvMz0SZ`FIN-e9Z7aWVGKm!-#A<7<@FudbW?*g)<)P%Cv(pA6RTMvmpzYmj*cO(>=m41{HF!ZCM67^@*-@?yZmW5y8`LZreCu@@Z6LPcyWW{?SW$%%Owfw<OW6U#J{fN#t;c{As$fwnMtUI!JAhL$dQ#jj+6hK~>TpX*jLg-U4@yC{NUC^d*CnWz?H4a@)*7p}mhpU(g=;2#u2QHf#|_i@-;gk6BQglhBNy~3(IF_e^&M-8C`PCotyeMS4aS7#+rqRIM7&(B<EcL!D=p|L;J2IPkQSG5n~IaZpY`;+Y=Ho`%>4*RV<i8qx)keSV>soTGA{||QnE?W')).decode('utf-8'))
_LEGACY_ACTIONS_6C12S_4Q_SECOND_YARN = json.loads(zlib.decompress(base64.b85decode('c-rk<U2j`ia{MoP)`Lk=5|uZN&D}9pGcsg*h0Q=143G^11e=FR-h%x1IFd+S-cwy&)#p(5IC{ILDc<vax~r?JfBEl|fBo(EfBgOTlYjc<<cH7iZ{Gd-;ripJ&v%=XhtrdP`|Use<v+jt&zHx4{Pz35|NXzdJpXd?<NL?|)gFHM{I_4Pe}4bd_07rY$=loelhbAM@y8!Gn-7!!__*1;`||PqkDKdHC#RRQkAK?S-2QxWy4ZdF!`<z>&u>5N|Kj4|;eSr29sBV9?O#5B*uQBp>Dw<S_nVKO9^3l!?cJvzAD?y~%^nU1;^XG#X8+c+`CGR?H+dCk$n>@Qr}<Q%2FzX;&K~UHt|gCivN-7L^S8*mKHOZt-9+Pw`m_B5@U~gI$y=ZQWICQrJ03s#dA}GA`uaRm!Pn9e-dxY$zh55LpEh^%MKu5HaP`2YyPPkgkGG%ai>O_kfBL_jaq!8kcWf%#!8sh@*(mM%_xAdEX>Pytv@<7Nx8`y`T<uG@qcHteI$dD@p~(R|p;^J?Eze^Q#%wYi&5X6*(P!*=-09FA{O)|`?T4_PreIwzgu@MNhVW?RXUjnsw2?)JPCj|tmg-|Ef0EB57{cch2Fy`5Z~7qa-m!c5a`t{i58lA-$Gzu=pT9{beeCbk2_Mpd?cYw`H1v1Vhp+Invs>jXuqKnk)VM&#{ObH{b++$|w_t9Mkgqmo#F!Smy}h~Fy#4g+pEh@&-rv0c=fg8$(BPF{Vl0vJJB~C5+gp3mo^TKC9Ff_VgRA`f!LR_o>Gf~S@4Szzx_6t}f1Nf7Fz*`kabkpng<J76fH4C11n$-I(zeWG-iK*#vp%K+2poIEAZ4x!e9C^1jRks2e~@_uqW#$6kH$?dI#BVTO17`Efv9hu&p+{W`dnWHcuIc`ddr6M0F3+nPqxNjzWH0=gxHpO`>dZ!O;v)My|7{Z`fKBVO}_Vm4Yg81?z&+R+Y0UBd<dg2X0Z5|Q}6B;AvMx*$gW!HkgV7bySGjbEdTBl+uqYTYX}jt-gPI?`?bs1pcidrShyV%LXnQsl(pY5o2cbMOooCzMi>1a^-Hl)f?g$qkwb>g!8?btz8~P~^=Dsy_7C{8I)F98)QKbSFod5%PUkj&5`^U2cQ+m^bLTXCrRX&pcuHRYGP8&(Ac%)bIqfG=^<GDoUGTx!{CIu$*QjITZhQkR5Tn>=sCIoR4$*WhdMF0%;IuKw9hsmDNa2IN>)6v<y+KDt)oxIxBbCD;0AD#+cKbED9h7~<Qy%pFFQThv`o4*Qu46EBjt0HYz#A$N=JtnMn$)Y=@cOg8AkledIX!=G{kYv*W9l3e9~X{k^=!m^{B(DH|HJ0)?r*@7DIrX0hr+i*8s>61+{79fG-B~^1T^XeK`86)G|b336ji-TV`QNUJRQr#np!7QtjR-|IH=OKK6VegD?R@?4QJcl$dgTr$*%)Lon79^d<2TCAnLdE@l!La79o0iYG@_I+TL=6@FsAzou8|~gh!*}y#}_vR+#L<!H&*5?V7WP!tp7@%Mu%b7%J#^Rh((+t7l+L<yv8A#pDvazrDSAOpAf0)$@NoPtce1@!d(;*4z8@xVOf~($T4zgN!0Eh_f;u>gZOG4c^09vDfl$B1BLQ#*!}u_7BKZ8f_?)ril3=T6|2suO%3&iyo%?E`98%Hu{+&WfFSZJeBdzO_U$uH4(t3^Kh)!M1(R<I8%p-1>L*A=zKff=;)iD7L{$lh8aESg91*S7C@e-&eRxRz$clRx5u)gF3fD%MJZwj%&!HG*{yP`3}&<1rkY5n(wty9^flvLcwh<2>;;*qK^wr;%&s~e$xwXlY=DA~+gm>PB8MB)vxH4H%;wEgw>|4Yy3=X4UQ7d1;06Ys?V?Tw5(wu1I?1+Xr1D*0iex({xu-pr1=~S1`Bcv}XZfx63WR^qX&lc6G9`e4G1G5g;$O6ZVK5bO8;f9M7%s*=W%f<Q*Z|f+6QXUh;jIyGJ0Ds)r{e#W$d>FK?L%qA+r>@BlDwQH3Io))JD(=ELEHbc&O0`&v}^27ijGnX@&ed5fZW;t*U~&dItsvz+ZOiamdNShUmo7Q|Fem~0{dD|9IwH?fFq*$Dg8{r#T)E)G+^-7hWP3I&0h{(D(G+_D*=9ug~NC6I<o6^mP1Lq>lImbx+Umx^a3Xgl8S&a7&#Zst*tOTIUZGqCv<4O;%Vx?o}SBW3xM?zyf0fUt+jgK)|1Q#Wh)5;jq3(K23kYN;gFqMMRQ7aQ7PeCT|AmsSpvW{Mn~(|?+top^I!sDA2Qjx62RalVJ@x$7CS{|TH7^=a{zCMIYF5AY1&D|RcHqiwVt@nFizG(4pq?S(<D~Y=ni;u3Yeu}Y64@H3@zFQU^8`F!6;_I_2)nnrz@|e8CUFN&{auls+H?&K575Fl2)+StBc<qGL^IQkhKiixr++xhrKr^TOa(Alsh9dayRQ<LnM!;kPZpvc!(1<K7(?|!)s&y@Qvw?86GmE&#Ag@S<HZG+3uwkum~Xeo+e{8P=cYg&vb8^aCp5CXHM}R;!%^}pG694e4#T57QnWKnps(tg&Lg12>|ikDnS7i<T+Qcne=buHwm!96V+^mS0J*mD<BAe;{1~XO5DoG=WTkJxMPVj292*3T5hEYIQSUNh-k?golZJ;#QEqF|B?%1s7KR%3|E2$5NGHH(e#Kh*GHuy5iu5vWD!`}vp(1+p=L~CHDcUc^SE?g7V%a2szbDn*w#a9xzIL{^t*inakeC_7N*)#$I+R?NBps|b~I^LZPbRe3YpEv85-WK`oVK-*GSSfxweJ*zV3?qimd_`>$lLX*M&7;cj{QdG5!4RAp0@g`AT$L3_|PCapK4y!0o;(uX*sYmAo#cumr&ai$`4Xbt?=qJuI%f=TVmgp++ykp9R7t=MRS!%Nhh!gE4!Tgh$1`cx~1}+%ucJR2hmUg?7#~9j@t1#ISp(fHZdzNrDHCYy(gNW!nMxcd;<;0Q}0f-SB%zjg!~!0?oZNZUl|mAaP8=7R*QX@<HdHveBe|Gf4rAQmS!l*C^7VcL2Q|?_$QeC9qYg2Ny9ra`9l$0MJqbP1W!&35v~orb94Pxh~l#J7(OpCS)xA=Jn;^N0a`6oZU%vJkmzcJN^gc+DGKb!@ew6fn?Ppt{1a7H?qys)~UH#G-Vif;mw1dLBz>K6jFtJEihqZ$)T0SyV4=@$tIvmy6w^YLc<&t<4kQzT@R6mi9#CCG|wWO<Y**SodL8g1SMOq)Eq0}(SuuLlp&YkfHp@$$X_<%B_r7R%d;vv!XcAy1u2PY3|mg|(J2sn^qyv$gB|NR{Q31%<XQtKPry$kKR?UCo{m&SUa0k_s~}2|%MpCs+Dg-&>Pf!JvQtx47}+-MhK$@@S!pd4USQb;)KoB(^}NuSyxgeIN$A58)5BBdY1RvKsc1u}lU<|hGJUR=;KNcTD9IgYX$)B+0Cz;PER=L|<OL#417nd<r-LmVPUz@dIH1LBrN<n8O??v%_U1T?s@=o;el!*BXRnfr?SySdd#k#v2sbN93{jew)<23|^C04MD)mXB!{qCo6XALnRCNbos7FgO3X4T`EHdMiO7{b6G0!xMv0{773D=L~p@L#v0$dEg=<L<X@~7+$I_n0uOHNl)YQ6e1;}->D)h6)3OL)r5t|Jc+>U^-)hz$bm0Ut>#ZvYT966<kMq2t3o0RMsF!9*8tIs@x&HP+qHtS7tFX(tTf%^MHXTiOG<%?wFlktCR_$s*ggV!J5zlQ9&h2}2JxA3JNMKJE+z<(NZ-U8RIasDamt3MLq+8oNDzs8Ho=X-<gfkABDz8esAaEKy5U6)@xqNzMkqS~$=ki*UAa@|uVrPvKEAwg^{6Nb=N~93muzM!Fq7N)V`oRHVe9JeOx2T@Vb?1ny8TOJ|&z<BPe1_*1?^=19j-OpXaqBo2F2s1J)7iTmT+KuJU)5H36eI<DR*YV4XV6TYE!<wH#alb3KymJve}x%Zl_`k1@sua~%J5?Y=bK?C5=vO}&=C&jW{!eJ$Mi5<g1qsxn(!uKXPQylQq-g3zrO-lc^zeon-3X8>*>i3wm4akj`Url0T1mN&uL=$FzbLatN3_CIhKF6f>8TwTyTA!`KPlz|yD@_j*k1|CLN_8-EMm#90zgm<s6BY2H6VqZe5=pX!?S*Q}PP<A}xeIEZ6bc*B{5=MV=p-A?z3C(er74E$xVD#Mu_T(sf^OF<8(?;U`}W7`VUUBZineT#jTzB8EA5I61><s2v^0}s&p5%u%1@_BvK+*qCZ|!`j5P{XcVK7_vW-*et_q|m0xRlfFAbdLFH887%AwkfsT(2Q9(2`>8Zt2uu6W^6)<UgVlh`EMHnDJZk!Zw<+#ydKwM&8&i~)6pa@EfQn5jjRDePV2Aozq75m(TQg1mrQrqP(1zkk)Z^$`NF`rbGL1-C3f=CkbmPEW}RD#G;8v89DuJKEI9=<ZJ;;wbwiy1IoP4KK`jF;ypyNA`QfZl&F<I0+1q^!deMeUImVW+@*-y&GLL*H+r7)dobBLaY>?+K!{<>*3VY>SHTX6529N<RZFcAymQF$`ph5?x|PV0QU*Yh;E7?jZ)KE1;l>QORsoIGT|zLkqv&JG~~eHk-YC>d29}LvP7I5T-2Nu7_MhNe&xk9X@sT};N7QUXo~-%RjW}#(F16cN=ixMif@kN-$dTbIre+Lb^iw0QQt&_5@C;G5U(Qxo<%3sq-3yvsKMs4q16zi@|*|`j*z}rIMF(&tc%PE40fIrUerjF)>7JG-Cq*NPA944iSSI998mAtxX|Q)q_&kLEvKjzwP&+_SJR_F=fSfObl=Qb6(6<gj&xSit>=q@T^O?bZ4!v3@xc@^Thl^cWr85#{%6~45bABH4v4LyxHxmjx^n7@T8M%cR!|X?rIS%lb7tL<XDLO6c9S)4<!gC$<cVHm-iLE%(NEim+)B~m=E)-^`N2Xym(E(_+1U~=xlg@w>D&*{{S64z8!xH5a6EzDtla9r34$S!XKB=O&@^2LbYLDX!W)cIpN44hqTZ~9MaM2)hK68u((vnyfZsP|YXMgg0Umz5X$z61&>4M#WOYTLPoq$Xn@IpANA^$2S{jzl-&9{hq@cb|jzPN)etRm|xQ=N3tH#$l{Ae->Wt<63%{N2eFDU&1zkt&LSTb)X%@!y$)g=PB&*(7&0kBXB-BMz{3&kO8P>t56Ev3+c1-OwsZ7qa5?`N@QT>(K2d8(a=WBZW6qKU~+QC4Uk_?;f*%+}J-(^biB`55N&DUY)Ko<g16>o|;^>Es_KpJ_C1rfPkW=36uKd-o#_^j8#q)gd)!leU&J0V#AL;loMJt}a`NMzdY{p%x{s3&LMp*8v`{JcLb)19b}|QpX1!8?;tI=;_(*VqT{_UP(@W8flIvPfN4jy*4<(`U<|R9x7Wi)09ZQNS1y~78Z!zQtcL&%|Q|kY-NL|z>^}}-@8JR6s>4_#`OU0e?`_5@>yi2kJaYosB#Gr1>`F5b7z&wUs)l96#~t17QFi!oDjwa6`W<5rG8eW^LaVy_c9{{+%D{%>?F^l(5PjuM*Ts^T7Rzls8n^}e#?HuGrG1Ek$rfgO@BiP%hM7FYOPhH{G*fW-IaIBY6@_OAahM<&B0DA0XU8AaLa;`eQ5)50j-TP3BZdK3bCbBgnEU#wPRc|?nqK`Akk{}2~SrJsiR%yVR^iZd9NgAyR2E2m|KgBl2#jI+^F(~sy=_Hdn8t()RgT@#geI?5ZmEnLiQ{Lfo>_`@;_XYne<zs_Mt)?A^9a-dW@aQjJv}sB-ZL8*6Kx2%!lGY3SnVLVaky#uM{13aSo6ROVAieVK1XyiDWAo^f(hCg9KoeN+j`m>{LR8<+B<azglZWCG7dRN`t$o@+D}<mcVNSaN8Yak6eT^S3s2sUzp{ITWN!U8V`0W4+dzOPiFDck!yK1tjeguC7FO^FkAXn^^u`xNs=h79CT#J%tLLeQgc8PqLG3uay=NTRuoqtS`>A(O<_OOilUB@h?G3|BV}Symrsu|ODFnRPf(-P7#fMbx+6=B9^)1&Nm%Wk3!<ae8rL$2>phb)vUHtWt<oT1ry0|wC#ST*n@s)Inwv1%B2JB{Ipn2l0n;`Tg^_{S(lpJD)RkbQl6?k_O4WX)>5-f;fjbvxq%N$KmUew&PhMp0jGeEgFkgfo0B$sx%0u(&1%C;w=sqVyxbuK7CD;98E|gpwal}<{)y()=xf%fB@k)g#+4T>}=(_{$_;VdgfHakYwHzO|ln;+;_RV+i|J-foT-7s9#FFLgxZ<Z;+jk=)>XJ>c2qwfwn=++}PRzcu+sR~Q-+ICTR~=+2jpilPAubn^c^sWmzt6;!v38U5l-~^xb13<Nxp;1u6}c39&a2W;FmTM%5za3q@7_%jrVCW~sJMK45zZ-^`4s;+fHRk2knOCo4ouakE(`fPLqBcq;Ovv*^98M(G*Pt3Q#~uP1u>~5v%N)*;dttxhi`)8_Zwsg77Ov-Z(K*Iq8CbYfnxF&3&rEG^)QL)DhH5tVk4R8v2hJtMpMj~U>@>9QtN{DPs+kz2cjg&jj)W2oIwr3*Fm-P)u`U{0l9a@a@(|eHnb~Eu(ja1XX%?PM>-WO(Q49Y>OYapio$C$0tixozM#8gi21N;UZ?>{*f`_R34`t|D0VWVA;pV`0b5-DMit%5aa$NiCLkUKbi~``ShGTpHx@Jyojd7CC~sbz6$(V)4Imie^{H9*;pFLEM{=#z!>TUJqwF1~37yrRODaVL8A4OlW;fK`R=SxNu<c}fo7QFw50Z$1G>`pIr^N-N`_e5d6~0I@R+r_lO-IE~z85EE<4#&i#QDx-m~S-}9lHqN<3C~{s6(l&<*|^v*3AP(+Pu+c;fIAk2}RlZATt-sW0K62+LhO8Ai-82laY&hSZd{!nmGZoNEreun^dhBRV%~7&%4Z_)@9<wj&<s7aS3?Jx!L5fObGx(D#_|{p7aZIo&eLv#%7rLap|0qt;r-M&?cU+UhKL9{z?;Z^~wo)5Q4in<KRnT;xkHNBpDJ_sM=UHe8Sjv%@HHn&3wS~GF!k%bhpu35xj<yLps4&cSU(bJQ9Es3@FOCkYJcxPL5;cC62p7<z)I+sG^gI-ZRml&@wQNzBg9(Sd#hX0x?*0Pv^Rw)$+hHJc$aB6COo)(eY!gB9xXu!f2P^Z^l&pY$A;I>-o9?huaJ_<)eOS)uGlXPTH}>r%)X93ri4#SHsLS?Xndnv60ObR=R0{^pr%FRsc7mjHl1eRaj>`N2n<IS0==Z*tiNWMhTz--_FLUfDqDlmHc7r_yPE>uP?{0@AqQasH!A&Vr7(pnwP8V7kweCSyC?4UP?ACa+m7A3?^2PgUZc5FA0^)Rp;5-84xz)wiuInn$2)<S|oW|Pi?D#5qf5zm6m!h7Ej6!83$epb2EJBk<|&Trs5|zL0}bz3wTyUt+FXKT1>JyS;oT52haO)fr;Qjgsy}o0-kJ|FHYyk)O2teHVfsz)yfsNYZ>tDcxTaB9eA<D%?U+NM1+f#Jfx-E>BVD3tp;UF7WS@Dk2ENAyw!-Ei_#?eO2y(~2k~%gmoJ@NUN9RHDqSYIaNju?mwmbGGS!{IBAV=2rQYYd)H|6gOHV2>jlJ{u!i#n_LO@K)Wt0TskO@{k$k#P1E2FWBvkF&lbCO*SkO)h6>FLNSAv7Z7)o-qp3$M`=`L@g1b~1ap;=5KCs)*>dhYGT<c=6KC;*L=&!w8}xZ?DKfVz<xW6URnB4?N>VTfy-%vR<OI;5*moBX?cFex0}QJp2$YME%eC7VBs4wb^o#UNb4B78l|h&gC--8SsOQ=GPV3ds&m5tX!SSN7%<TQXgZnONeGdcOR3VON{U=cam2m^@ZM;ZEghc5l-8#W}dl5H>FEFS{U#v6N}etjvx+#>Nk1?wp|(=(~2h*f@$79Bb6j|Z;ebON3u#=f?OP*Mxjd-tMeL_$CL*U8KsH>zAA$_z4pa@27{8!kYy(^7xpo8;*uh3SEX`#h^(wtiV!O}aHHNPZM3V9vqpBSZmW6~;qp1MZ61JWs$W$zpOLS&1MsEWcel})hy-;fP>y`G^O2oSq7hm9QwjmsFHIRGml0FvO+E<Eb0t?%&`Jy>>OTaD5fiahDXsHrGBT@@D-}@iYsrRa|51hT$U!Z!T*PA<9s1i-aR~HFq+CU1JXSVB;~8qYf5G$%R8x}rxQ@<%j-^4tNc6OwP>nUq%}co8`r;zV0^sMqm>9;_z9PRcNaA*>?th!6`8<5*4Mw?UM4#`3z4>&f9+keCh000LrI76sOCA>3ovP}eRo;Ns>|L8Vn1a8ogL4)Qv{<0TL0y&AHMW#U?$GoCgRMI~eqH8ZR%d+`1*&qCsI}@;a2b+^0^c#0SUES2z^v&$?935^TG<;VHcb|#O4Co)Y+iloIsDstgrZk**~flt&8Ze7r4>-Kxjl?;uY;u$S9%wR;YuM2u8mb51n4h>G(Sq*b>YcKFNvVd7sfgd1xw_@2m+Eh1pOx{7wZIu^YM)EGGl!qfU~~-#5!CnCz;5cqnJS+vq+4flv<vX5y<mdl{89Eg9PTD;67hYqN=;@Vb60o+ckLUu%Qz^r34rnhG!RuW~@1$cEXTwohChuOQ(SYjN2@71!Fp-$o2Q@3oI?eWnB&nXgqK2(#vv@_<T#zfOTKk4&W2GsYLy;ss1u#zSqSFa!~~qgt^eR-S)Mk>WP<`a8a)j0)(&%*yjZP#km}D?5|FRUXPD)b#XVtNjoM0x<as~`Qfqnn3hi17)~jpW?uN3(`|&Mo!5djmlVxN@*EjFVChY9h3tazVg^h&$%`d~=CYJLpyvL|3?iayP&`F?v>?P7L06`Kr`VR1Fl~uUw8Makb?P-?%W>&dX-THod0W3YkasF%Yz~~l(;h`k8W&>%IDxtntJs_x*UPIu1&YIVD5PxUCC(~hj;zT8wpY4Pnr#=4JkFkAuJOjc&?F6aR@<7()S1O;6%EUBZBioEN%Mon9KMktE0tLT{)b%)sofMtSoo}>szWMMQCvGOk1#}+lDWJf52EGkYn3#(Vw9Y7u&nQb!kr$~URA5Ej}fShFMOeBY7p)s)T_3KD(R)|%&PBF=g^r}ewLuaQV-42s=Q+GMwe2wD6XzN*jarWQC(B7P)J<mxsHbQW*x}>k6qhFF&7FeP+_Q2@g!j8GWz~@(h@b{-V=Q}NGNg%?!b%x2Z_%|6ohoWWYmQ*nvm79wy{LQu!6jKfZu6+2DX%(IFDso$9wQ{iuD#WZB$i;wr8d3G^*a3zPSwKsz&_-o{}gRkE#}=Dvm3I`Xy2Pcxg^>Wbt^p8ZEpW#NLD1<sMBm!SY*$hEhcng@*@H@ieqet9U}9Dyu%6o0Phy@;B+6=_h+u*0(Gp$Cz|{o>B>Y$7jFlqnG6;sg@@ru$9UiqFC3RWcG0`P)wa6J7pO%$@)r^WbB>L+i{dvY_6HASVzQts9Xsx>L@XiiaGyhW$G1!tf@AiR5+lPZ&!<JStU_L`4a|J7?rawZGO$dsXl6hT$HL>%#nQ4kt9o8r3UmN>7ZhggS6+;^?2HW`WqE&_0>zskx$bjGG6=0kp4o}5KFfjiLE<$K7tsxl9(_pD#l<nO1KV#)nk|ueYCYVl!L#e&@H>kZTe>X`c;Ley!V#@=)^o<w9JHLg!P!xEl&1s4%9`)HOkw%tmY>y`uJZKSXPmiQ>9*(%R#)bq5Y8AMQ*b1g%M>`mT-R|4MV7IqcTgeK~@6=b>T_P?dAhgWW2080YjZ)s+4Z7a^0>5A&DthL5mJE>V_136hJC3r<WD@NaB@R4cqj%)CGb<%ZJ7s6l7A>h5@RWG3#MaZR-|D$lwrKJe^ki?5t|Zn4U@UCMyoqz{NA8*eWHev^v?ZXnciA?mTt4k~n)W5I8||fXUR_g;q37Nu|i@dud>&lSbi`4cR@2KuDzg$lZmy9Ihk#m{;M}Fc7Ab+eLz`CUeruhld`y(`IV@9;r}nlny{t7jg;1A=<vwuqBRemWiqA7(W6$BW8q<&(dNu>`0aM0wWOJ>D)e7vTwc7Vt&*-A3#1oT8ZLBRu_~*Ily0It+hXr99|QA{AP<8b2kV!$tqltu%3$bMP)3=NvusGE|!v=7QR-%bw*38jG2-`YgVF=giMO1cWF$)s5VumWdW_N){UnQ7q+|y!GBk^LdarqjQk`CKN>}pQ_30x?~jyjiI)GdW<;sBP0MaGci}z{4R<adozW)b|49OVeQJuUvVTLUN#ws2ij!K2Q}>*cZAn>XQk6n!@l**&#LL$}tVG7Fcf8wOz}bW}J^(oo0jGgz8j8Bh!>d@pDrjJGq>{9Snibu8TyDu(tqQH8iZW76-q1ZED=!yhtZf)Eb(vFkC_gPToIEXx?(Lyf7dNU#*@e5!+)S1l-x7EjZAamBmEl)sT`^IFHqo+8evb>-4b6%bYeX>VYD5hiR7`nL&14%VdXDQylx-k*x;%^Oy8@K^vI}(qeBAFV%h6ELmLldg!7O_ERf#B><pjNkm2+H<$Og=AF(~}u!7>tKgqhn$2GIPMt-`BR>pZdVX|TOggf{_GGptps_$cMvf_sCBm(eRFtE2}_jRKC5+p87@+FC~H%!$s3e1n$iz)?_M3jTnGTFqlbev!nUMCv>TZ(-JwOaUcZ|GGHO5>J-qin3{L&cuOhFbmX+vQj46;!bpS@N?l9?l)WQ{BZs8W9W-K{ohQ`eET6Y<ab}1xWA7db+!#Qq<!ErTt{jfY0rMl_Q+Dy3h=ELXc(U1wzac|7id}G;k8vqYSkPvqS1^sW<bD*wpvoKk3*4Ed@a<I5MNAbXEf%Xad2~QfQMO9bCHTkm0V_q1ZmlJd8d)gnU)RCm~n#Z#c%zLTb&Gi?p`G;{GJ@~l37k(-JV!T{0-eVaIw$K4C}>cHi2!>S~BEp%zF#{2J(*ZcC}s$H!$lgF`=v%@BX%ZYi>6Tf2C*`_Pi7rYPD<Du)y1nwhz&Fim#Nq8Ll+zrTbXT-R+0$1<@x&hi8q7+*SM^RGNxxv3x8DMAx1eOrDPnM*2$HQC>{U=<4&_PE+ff+1`CZ9%f%w<1gEJf0Ng4Jd(|QI5rRe3!QmfDg')).decode('utf-8'))
_ACTIONS = _ACTIONS_8C6S_3Q
__version__ = 'BL-Kawashigi-Adaptive-R1-V19Core-L3F50-P100B12-LayoutFallback'

_PRICE_FLOOR = 1
_DEMAND_ALPHA = 0.25
_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}
_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_SELLABLE = tuple(_MARKET_PARAMS)
_LIQUIDATION_ORDER = (
    "CARROT", "EGG", "FERTILIZER", "MELON", "MILK",
    "STRAWBERRY", "TOMATO", "WHEAT", "WOOL",
)
_WEED_STATE = {0: {}, 1: {}}
_WEED_REPLAY_STEPS = 8
_SHIFT_STATE = {
    0: {"last_step": -1, "due_step": -1, "due": {}},
    1: {"last_step": -1, "due_step": -1, "due": {}},
}
_PREEMPT_ENABLED = True
_PREEMPT_FRACTION = 1.0
_PREEMPT_MAX_BATCH = 12
_PREEMPT_MAX_CLONE_DISTANCE = 6
_PREEMPT_MIN_PRICE_RATIO = 0.0
_PREEMPT_MIN_FUTURE_QUANTITY = 4
_PREEMPT_START = 120
_PREEMPT_STOP = 680
_PREMIUM = ("STRAWBERRY", "MELON", "MILK", "WOOL")


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)



_KAWA_MILK_SUPPORT = {"PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"}


def _kawa_route_label(obs):
    shops = list(((_get(obs, "town", {}) or {}).get("unlocked_shops", []) or []))
    if shops[:1] == ["YARN_STORE"]:
        return "6c12s_4q_first_yarn"
    if "YARN_STORE" in shops[:2]:
        return "6c12s_4q_second_yarn"
    if "YARN_STORE" in shops[:3]:
        return "6c8s_3q"
    if _KAWA_MILK_SUPPORT.intersection(shops[:3]):
        return "10c4s_3q"
    return "8c6s_3q"


_KAWA_LAYOUT_FALLBACK = {0: None, 1: None}


def _kawa_use_legacy_layout(obs):
    step = int(_get(obs, "step", 0) or 0)
    seat = _seat(obs)
    if step == 0:
        _KAWA_LAYOUT_FALLBACK[seat] = None
    decision = _KAWA_LAYOUT_FALLBACK.get(seat)
    if decision is None and 24 <= step < 72:
        farms = list(_get(obs, "farms", []) or [])
        opponent = farms[1 - seat] if len(farms) >= 2 else {}
        counts = {"WHEAT": 0, "MELON": 0, "COW": 0, "SHEEP": 0, "PASTURE": 0}
        for row in list(_get(opponent, "tiles", []) or []):
            for tile in list(row or []):
                if not isinstance(tile, dict):
                    continue
                key = tile.get("crop") or tile.get("animal")
                if key in counts:
                    counts[key] += 1
                if tile.get("kind") == "PASTURE" and not tile.get("animal"):
                    counts["PASTURE"] += 1
        decision = (
            counts == {"WHEAT": 5, "MELON": 5, "COW": 1, "SHEEP": 4, "PASTURE": 0}
            and float(_get(opponent, "money", 0) or 0) <= 12
        )
        _KAWA_LAYOUT_FALLBACK[seat] = decision
    return bool(decision)


def _kawa_actions(obs):
    current = {
        "10c4s_3q": _ACTIONS_10C4S_3Q,
        "8c6s_3q": _ACTIONS_8C6S_3Q,
        "6c8s_3q": _ACTIONS_6C8S_3Q,
        "6c12s_4q_first_yarn": _ACTIONS_6C12S_4Q_FIRST_YARN,
        "6c12s_4q_second_yarn": _ACTIONS_6C12S_4Q_SECOND_YARN,
    }
    label = _kawa_route_label(obs)
    if _kawa_use_legacy_layout(obs):
        return {
            "10c4s_3q": _LEGACY_ACTIONS_10C4S_3Q,
            "8c6s_3q": _LEGACY_ACTIONS_8C6S_3Q,
            "6c8s_3q": _LEGACY_ACTIONS_6C8S_3Q,
            "6c12s_4q_first_yarn": _LEGACY_ACTIONS_6C12S_4Q_FIRST_YARN,
            "6c12s_4q_second_yarn": _LEGACY_ACTIONS_6C12S_4Q_SECOND_YARN,
        }[label]
    return current[label]

def _copy_action(action):
    action = copy.deepcopy(action or {})
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],
        "market": [list(order) for order in (action.get("market") or [])],
    }


def _seat(obs):
    return 1 if int(_get(obs, "player", 0) or 0) == 1 else 0


def _farm(obs, seat):
    farms = list(_get(obs, "farms", []) or [])
    return farms[seat] if seat < len(farms) else {}


def _align_hands(action, obs):
    action = _copy_action(action)
    expected = len(_get(_farm(obs, _seat(obs)), "hands", []) or [])
    hands = list(action.get("hands") or [])
    if len(hands) < expected:
        hands.extend([["PASS"] for _ in range(expected - len(hands))])
    action["hands"] = [list(order or ["PASS"]) for order in hands[:expected]]
    return action


def _shed_access(size):
    half = size // 2
    return {
        (half - 1, half - 1), (half, half - 1),
        (half - 1, half), (half, half),
    }


def _projected_shed(obs, action):
    farm = _farm(obs, _seat(obs))
    private = _get(obs, "private", {}) or {}
    projected = {
        key: max(0, int(value or 0))
        for key, value in dict(_get(private, "shed", {}) or {}).items()
    }
    inventories = list(_get(private, "inventories", []) or [])
    positions = [_get(farm, "farmer", [0, 0]), *list(_get(farm, "hands", []) or [])]
    unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    tiles = list(_get(farm, "tiles", []) or [])
    access = _shed_access(len(tiles) or 10)
    for index, unit_action in enumerate(unit_actions):
        if index >= len(positions) or index >= len(inventories):
            continue
        position = positions[index]
        if not isinstance(position, (list, tuple)) or len(position) < 2:
            continue
        x, y = int(position[0]), int(position[1])
        if (x, y) not in access or not (0 <= y < len(tiles) and 0 <= x < len(tiles[y])):
            continue
        inventory = {key: max(0, int(value or 0)) for key, value in dict(inventories[index] or {}).items()}
        if unit_action and unit_action[0] == "DROP":
            deposits = inventory.items()
        elif unit_action and unit_action[0] == "PLACE" and len(unit_action) >= 2:
            item = unit_action[1]
            tile = tiles[y][x]
            structure = {"COW": "PASTURE", "SHEEP": "PASTURE", "GOOSE": "COOP"}.get(item)
            if structure and isinstance(tile, dict) and tile.get("kind") == structure and not tile.get("animal"):
                continue
            try:
                requested = int(unit_action[2]) if len(unit_action) >= 3 else 1
            except (TypeError, ValueError):
                continue
            deposits = ((item, min(max(0, requested), inventory.get(item, 0))),)
        else:
            continue
        for item, quantity in deposits:
            room = max(0, 100 - sum(projected.values()))
            amount = min(max(0, int(quantity or 0)), room)
            if amount:
                projected[item] = projected.get(item, 0) + amount
    return projected


def _public_signature(farm):
    keys = (
        "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
        "COW", "SHEEP", "GOOSE", "PASTURE", "COOP", "WEED",
    )
    counts = {key: 0 for key in keys}
    for row in (_get(farm, "tiles", []) or []):
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value in counts:
                    counts[value] += 1
                    break
    return (
        len(_get(farm, "hands", []) or []),
        len(_get(farm, "unlocked_quadrants", []) or []),
        tuple(counts[key] for key in sorted(counts)),
    )


def _clone_distance(obs):
    farms = list(_get(obs, "farms", []) or [])
    if len(farms) < 2:
        return 10**9
    left, right = _public_signature(farms[0]), _public_signature(farms[1])
    return (
        abs(left[0] - right[0])
        + 3 * abs(left[1] - right[1])
        + sum(abs(a - b) for a, b in zip(left[2], right[2]))
    )


def _shift_state(obs, step):
    seat = _seat(obs)
    state = _SHIFT_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {"last_step": step, "due_step": -1, "due": {}}
        _SHIFT_STATE[seat] = state
    state["last_step"] = step
    return state


def _repay_shift(obs, action, step):
    if not _PREEMPT_ENABLED:
        return action
    state = _shift_state(obs, step)
    if int(state.get("due_step", -1)) != step:
        if int(state.get("due_step", -1)) < step:
            state["due_step"], state["due"] = -1, {}
        return action
    due = {item: max(0, int(quantity)) for item, quantity in dict(state.get("due") or {}).items()}
    market = []
    for raw in action.get("market", []) or []:
        order = list(raw)
        if len(order) >= 3 and order[0] == "SELL" and due.get(order[1], 0) > 0:
            item = order[1]
            requested = max(0, int(order[2]))
            reduction = min(requested, due[item])
            requested -= reduction
            due[item] -= reduction
            if requested <= 0:
                continue
            order[2] = requested
        market.append(order)
    action["market"] = market
    state["due_step"], state["due"] = -1, {}
    return action


def _future_sells(obs, step):
    if step + 1 >= len(_kawa_actions(obs)):
        return {}
    result = {}
    for raw in (_kawa_actions(obs)[step + 1].get("market") or []):
        if len(raw) >= 3 and raw[0] == "SELL" and raw[1] in _PREMIUM:
            result[raw[1]] = result.get(raw[1], 0) + max(0, int(raw[2]))
    return result


def _preempt_shift(obs, action, step):
    if not _PREEMPT_ENABLED or not (_PREEMPT_START <= step < _PREEMPT_STOP):
        return action
    state = _shift_state(obs, step)
    if state.get("due") or _clone_distance(obs) > _PREEMPT_MAX_CLONE_DISTANCE:
        return action
    future = _future_sells(obs, step)
    if not future:
        return action
    market = list(action.get("market") or [])
    if len(market) >= 10:
        return action
    remaining = _projected_shed(obs, action)
    for raw in market:
        if len(raw) >= 3 and raw[0] == "SELL":
            item = raw[1]
            remaining[item] = max(0, int(remaining.get(item, 0) or 0) - max(0, int(raw[2])))
    prices = _get(_get(obs, "market", {}) or {}, "prices", {}) or {}
    shifted = {}
    for item in _PREMIUM:
        future_quantity = max(0, int(future.get(item, 0) or 0))
        if future_quantity < _PREEMPT_MIN_FUTURE_QUANTITY:
            continue
        base_price = float(_MARKET_PARAMS[item][0])
        if float(_get(prices, item, 0) or 0) < base_price * _PREEMPT_MIN_PRICE_RATIO:
            continue
        target = min(
            max(0, int(remaining.get(item, 0) or 0)),
            future_quantity,
            _PREEMPT_MAX_BATCH,
            max(1, int(round(future_quantity * _PREEMPT_FRACTION))),
        )
        if target <= 0 or len(market) >= 10:
            continue
        market.append(["SELL", item, target])
        remaining[item] = max(0, int(remaining.get(item, 0) or 0) - target)
        shifted[item] = target
    if shifted:
        action["market"] = market[:10]
        state["due_step"] = step + 1
        state["due"] = shifted
    return action


def _tile_at(farm, position):
    try:
        x, y = int(position[0]), int(position[1])
        return (_get(farm, "tiles", []) or [])[y][x]
    except (IndexError, TypeError, ValueError):
        return "LOCKED"


def _trace_actor_action(obs, step, actor):
    actions = _kawa_actions(obs)
    trace = actions[min(max(int(step), 0), len(actions) - 1)] or {}
    if actor == "farmer":
        return list(trace.get("farmer") or ["PASS"])
    hands = trace.get("hands", []) or []
    return list(hands[actor] if actor < len(hands) else ["PASS"])


def _weed_repair_action(obs, action, step):
    action = _align_hands(action, obs)
    seat = _seat(obs)
    game = _WEED_STATE[seat]
    if step == 0 or step < game.get("last_step", -1):
        game = {"last_step": step, "active": {}}
        _WEED_STATE[seat] = game
    game["last_step"] = step
    farm = _farm(obs, seat)
    positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
    unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    active = game["active"]

    for actor, transaction in list(active.items()):
        index = 0 if actor == "farmer" else int(actor) + 1
        if index >= len(unit_actions):
            active.pop(actor, None)
            continue
        age = step - transaction["start"]
        if age == 1:
            unit_actions[index] = list(transaction["intended"])
        elif 2 <= age <= 1 + _WEED_REPLAY_STEPS:
            unit_actions[index] = _trace_actor_action(obs, step - 1, actor)
        else:
            active.pop(actor, None)

    for index, (position, intended) in enumerate(zip(positions, unit_actions)):
        actor = "farmer" if index == 0 else index - 1
        if actor in active or not isinstance(intended, list) or not intended:
            continue
        if intended[0] not in ("BUILD_PASTURE", "PLANT"):
            continue
        tile = _tile_at(farm, position)
        if not isinstance(tile, dict) or tile.get("kind") != "WEED":
            continue
        active[actor] = {"start": step, "intended": list(intended)}
        unit_actions[index] = ["DIG"]

    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return _align_hands(action, obs)



_V17_R5_MARKETS = json.loads(zlib.decompress(base64.b85decode(
    "c-p;M+is&U5d9aPc>von<S}hoHCozKq*c_7M*IJNu~cDG40E%AN|hRs_<}v>%$Z|fuh;D1<MZ!ZcY6AGe9!Xi^4uKy|D}Wcnmr%8CKEn<H9x!_Uk+{G`tfw>+s+=JpPS|_%iaGk&Q0^wKYnT2(`%ORCXa_H?7oNTKV7qP)3)E=?(x1X-k166V)@@_J}dP%ywtCzdq1|vKTQ|B_jH|S+f>1*FMK1(wk5C)J+KpJyHx#R$wGv?TTULI-@C)*q3OEMuYj0sUBuM5pQ^e^Tl*5$h?vO>bLbk+X1ca1(@YPY#7G!#xnpQ4A_!J^>EuBSth-X^Mss0J04yE}Q{FBs5@rl~CvSW?o!TJ<AZu{X0qx=SX|&m4I2dGIn8EsaD-&W=t~BJzav|WD=-=ZUY59SYsmdzy3%W;fI7<X0I(8+b6Pvb+6z|e08QDEET{PV$?SP|i4M|P213nE8;_6zUzA1~P5aLi83L<U1D1&bp<mK4@9!m=C7$K9?AwMl&lhHG5*?kgEg}S;D*^(eCd>wC{-U5O^Ld_5hQATi?WCpCEm8XZ<F|+eTcV&><r$Y%-z@fW1>(Bv1px-5-goHiCX{F5GYrn9hifb{O>C;Rf-4ug(U?`sCw$h-23djb=Z4oPofDqyrCnZ7srio*dq*M(=D)=zTjnYE0N<!nrK`IK^cA8gHDEje!?qLHZms~zs5_zQsAzQ6UI&}I96hR%d$AW6Y9=X8Uq)NmUf`fFCt%{Uk?F~?xsMgk|oX{~VLL^=&>5zV(c&JTsQiN-Zt5BLMc8E?lp$ZcU3l;N^d%QWzVWQe0(PG>NvWRF$<1{2pw3sB*uT8aH4J`9>!*WBHO|cy9n26;H9GZSHI;-eW>J=5=0$<F)GN*3+o*gXqmSapihqFzc7^gX7G*ht~47}e)7e(cDu4IaL28JK(lf;)L6Jnf7H6#+l)UC)TcrTuYdNGqe@wNp*zdw@mohJ#ef><v=t*HjXfi4P(zGof`I}>W!lGQjvY(5)#2b38yRR{E$E*@t!GMf9DTq4Q}1A=p^VC|{ol*~%G75Sq)f<JiOSIl>|QkF?W{ou5@78f%)Ixkw}*kTLkNufIzot4(w(lbh<$i5VBjD^)VmH^z=iye_cM)HObAM6n<cZwPZChjhaz`?4*Y*c;6TX=kZ#!-P?Nrx>uFdDx)b3!Sno*}jiU?W22@0t0>xHXiBB8=byze2@Z*QkAy2B<J@wozf2&B&mGx;#PD@M`T*A)Uxj5w70E_$!tJt=E%N&Glo1n^=PE3G8huMlegI_~GOr_}w%-qt75L@Q2!X7-|Z?8`F7CC5C5J@(sHPuJ`;(VI@-@f3+!o>&1&9#GwiHj_PYDgRMcQ3c8XkF$C?o0KlYLp)wKfSDu*5C^L`9ud{Ed-W|<Uk^;zC3Q~wY)ceKkvYb=w8iXKu6u+P|tD)`6s8S!Z^Yma0IWGhPHTh5lz5xRsba$8T{m&A*!4L2aQC`i0!$X7wxuFpL0hMf{p8"
)).decode("utf-8"))
_V17_R5_ITEMS = ('MELON', 'MILK', 'STRAWBERRY', 'WOOL')
_V17_R5_FRACTION = 0.5
_V17_R5_STATE = {
    0: {"last_step": -1, "target": False},
    1: {"last_step": -1, "target": False},
}


def _v17_r5_signature(obs):
    seat = _seat(obs)
    farms = list(_get(obs, "farms", []) or [])
    opponent = farms[1 - seat] if len(farms) >= 2 else {}
    cows = sheep = 0
    for row in list(_get(opponent, "tiles", []) or []):
        for tile in list(row or []):
            if not isinstance(tile, dict):
                continue
            cows += int(tile.get("animal") == "COW")
            sheep += int(tile.get("animal") == "SHEEP")
    return cows, sheep


def _v17_is_r5_family(obs, step):
    seat = _seat(obs)
    state = _V17_R5_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {"last_step": step, "target": False}
        _V17_R5_STATE[seat] = state
    state["last_step"] = step
    if not state.get("target") and step >= 24:
        cows, sheep = _v17_r5_signature(obs)
        if sheep >= 4 and cows <= 3:
            state["target"] = True
    return bool(state.get("target"))


def _v17_town_demand_at(obs, item, step):
    demand = 1 if item != "FERTILIZER" and step % 24 == 0 else 0
    if step % 4 != 0:
        return demand
    town = _get(obs, "town", {}) or {}
    for shop in list(_get(town, "unlocked_shops", []) or []):
        products = _SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += 2 if len(products) == 1 else 1
    return demand


def _v17_pickup_reserve(action, item):
    reserve = 0
    orders = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    for order in orders:
        if isinstance(order, (list, tuple)) and len(order) >= 2 and order[0] == "PICKUP" and order[1] == item:
            reserve += max(0, int(order[2])) if len(order) >= 3 else 1
    return reserve


def _v17_r5_counter(obs, action, step):
    if not _v17_is_r5_family(obs, step):
        return action
    future = step + 3
    if future >= len(_V17_R5_MARKETS):
        return action
    targets = {}
    for order in _V17_R5_MARKETS[future]:
        if len(order) >= 3 and order[0] == "SELL" and order[1] in _V17_R5_ITEMS:
            targets[order[1]] = targets.get(order[1], 0) + max(0, int(order[2] or 0))
    if not targets:
        return action
    action = _copy_action(action)
    market = [list(order) for order in action.get("market", []) or []]
    shed = dict(_get(_get(obs, "private", {}) or {}, "shed", {}) or {})
    for item in _V17_R5_ITEMS:
        planned = targets.get(item, 0)
        if planned <= 0:
            continue
        # R5A moves this base sale to step+1 only when town demand does not
        # refill the product before it acts.  Counter only that clean case.
        if _v17_town_demand_at(obs, item, step) > 0 or _v17_town_demand_at(obs, item, step + 1) > 0:
            continue
        existing = sum(
            max(0, int(order[2] or 0))
            for order in market
            if len(order) >= 3 and order[0] == "SELL" and order[1] == item
        )
        available = max(
            0,
            int(shed.get(item, 0) or 0)
            - existing
            - _v17_pickup_reserve(action, item),
        )
        quantity = min(
            available,
            max(1, int(round(planned * _V17_R5_FRACTION))),
        )
        if quantity <= 0:
            continue
        current = next(
            (order for order in market if len(order) >= 3 and order[0] == "SELL" and order[1] == item),
            None,
        )
        if current is not None:
            current[2] = max(0, int(current[2] or 0)) + quantity
        elif len(market) < 10:
            market.append(["SELL", item, quantity])
        else:
            continue
    action["market"] = market[:10]
    return action


def _shape(name, value):
    value = max(0.0, float(value))
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1.0 + value)
    raise ValueError(name)


def _market_price(item, inventory):
    base, equilibrium, scale, below_func, below_target, above_func, above_target = _MARKET_PARAMS[item]
    if inventory < equilibrium:
        amplitude = below_target * base / _shape(below_func, scale)
        price = base + amplitude * _shape(below_func, equilibrium - inventory)
    else:
        amplitude = above_target * base / _shape(above_func, scale)
        price = base - amplitude * _shape(above_func, inventory - equilibrium)
    return max(_PRICE_FLOOR, int(round(price)))


def _is_sell(order):
    return (
        isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] in _MARKET_PARAMS
    )


def _impact_score(obs, order):
    if not _is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        quantity = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    prices = _get(market, "prices", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    current_quote = float(_get(prices, item, _market_price(item, current_inventory)) or 0)
    later_quote = float(_market_price(item, current_inventory + quantity))
    return float(quantity) * max(0.0, current_quote - later_quote)


def _demand_per_day(obs, configuration, item):
    town = _get(obs, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])
    turns_per_day = int(_get(configuration, "turnsPerDay", 24) or 24)
    shop_interval = max(1, int(_get(configuration, "townShopSellInterval", 4) or 4))
    demand = 0.0
    for shop in shops:
        products = _SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += (turns_per_day / shop_interval) * (2 if len(products) == 1 else 1)
    if item != "FERTILIZER":
        center_interval = max(1, int(_get(configuration, "townCenterSellInterval", 24) or 24))
        demand += turns_per_day / center_interval
    return demand


def _order_score(obs, configuration, order):
    score = _impact_score(obs, order)
    if score <= 0 or not _is_sell(order):
        return score
    item = str(order[1])
    quantity = max(0, int(order[2]))
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    demand = max(0.25, _demand_per_day(obs, configuration, item))
    excess = max(0.0, current_inventory + quantity - 10000)
    urgency = min(1.0, (excess / demand) / 10.0)
    return score * (1.0 + _DEMAND_ALPHA * urgency)


def _rank_sell_slots(obs, action, configuration):
    action = _copy_action(action)
    market = list(action.get("market") or [])
    rows = [
        (_order_score(obs, configuration, order), -index, list(order))
        for index, order in enumerate(market)
        if _is_sell(order)
    ]
    if len(rows) < 2:
        return action
    rows.sort(reverse=True)
    ranked = iter(row[2] for row in rows)
    action["market"] = [next(ranked) if _is_sell(order) else order for order in market]
    return action


def _terminal_liquidation(obs, action, step):
    if step < 716:
        return action
    action = _copy_action(action)
    shed = _get(_get(obs, "private", {}) or {}, "shed", {}) or {}
    planned = {item: 0 for item in _SELLABLE}
    for order in action.get("market", []):
        if _is_sell(order):
            planned[str(order[1])] += max(0, int(order[2]))
    for item in _LIQUIDATION_ORDER:
        available = max(0, int(_get(shed, item, 0) or 0))
        extra = available if step >= 718 else max(0, available - planned[item])
        if extra and len(action["market"]) < 10:
            action["market"].append(["SELL", item, extra])
    return action



_V17_MD_MARKETS = json.loads(zlib.decompress(base64.b85decode(
    "c-q}u&2HN;41O1%eF$a8KgYE7&|qm(xE+eF5cd9Wv35zD*d`^CqMcws4}~q$6h(ggNK1Ktf6wl>eV6&1_s`9*w?CW5?Zal5<=O52HOt-P^7DPyJ)PZn?z+2=%dhv{<|WJP(dCD3w|~rX_#Xb$@9%!yzMP(@{Ku{L?77?RP8W;Mi|2pD!)`o|9ty}%tG{pce{}uJcDMcA^`CQ~ro2YAjxLauC7d^zU&-~VZ|yM$gOS7BZu)+2w_FyQ)1Hfl!1^@R;SD$Al-8fR3}dLlBN`-gK2G5IrQf{XbbbGJoCWzV^Z^_aFgc;IJln`Up0;O#m5Sh`gEKtYWWV2?dD(9Bc$eW~osZ9*5=%-N1!V0Lt;~1^U5ZMWnLriY!%!`K5R&Z?mS=@@%z_m@;bBxiY<E8~!&_MRJW5Jj892ATz_Y*9PFk3NLc|UB@(r=B4EVJ$ty1hmD2B?|6EhYhT9ux-Mhh#W;grG#dDJRs2i|a6t=jX${3AZ;l%#kF8qDz|qpJ{>$ON%Q4=M(02|!O~XkJW4Y=TZCp^9M&E{TNh>5U?)4~6r?1p7@qEFj+%-XJ7p!4|f15boIt6nt_9VI>%B?b7Ljd`V~vH9i7yK6r<pju8npJE+c|Y69|dl>&6U&vNIGXB#}S@q~ewiwh-6c6reH*~r?+RIOnkA!1xSoT3e^mBLS0gcqfcnmf5_JpxX<v~OY+9%a>$+GL_{)p$soy7h7_YZTJJ(YGooHbN!hiy)S7F65lJQ~_!%6Rw}rKbWU@Aoyqpg<11sdK83N+(OYRZ!NXVO6o|A$(j399*GLgXMUhGdcfJeVU)lSyN7+Sow{0mxx_%jY#t)URFq3Vt&qUQ8nc?@ZS_PX{bdUvQ8dV^@D<b8kr=NPeBPGnLurzcoRy2Mg`*iz5W`s)Sj$k8KHA@aiZEcK=k^E5jY*T0k;@tdM=ZUZaXQ6&#B{`YO>02-5>tK6Cb*W0QalhQbrb*ReN2WctH4?n(3M0AlBeq&`<xoevPi~5{aZj|TTx~&MWaD9dX>&G$kDYue@P}O=`6>fw5_FtT|y*k3su0%2ehv|z@KXw`1fT!cL|^icKrDJUgF=T(S}>iH&1gN^;YzIpp&?ls6uLtQV3;q5lpv6%2czxv^8jWsZA2aIL(*s(gOb6HDjn%2B9`~N?*FRFjlp!kl}PjAHW$c)=T!cctH``zFlG$1A8xu@CVogUhNhdJZX$_<Fa0!d)4XuI|Zr^q@z^NdrDe_b~{n<Sr8b9JvSrex6u%ivca*{wvf(olm!Z95yxw<k@NG}r>uyV_Zg6N7V&G4aW4^!w3k=pfG09VoJf%(85qafx`bMQ;(dD8gYwdif&|@Z41z|md6Z@~!eXw~u3wbznALcE8eP!FEr|UX>1QMwY<G{IiN|-hvFNk&+^r7LR<mZ$M8R}fr*K)vlnt7Ko!gl&xWcC}OWG;Yz7UjI=xMn%c~}d`xM>3WRU8W^28{NyCo38+I}$1E0V=3c#os0+tO-qcTZJ$IE8fD+uSH_%=Ip-+IrZ~{oP?`7*Y?9}{pw=<N*c=Yxr$z^ih8+~h)jq{q@qWh!lmHptnkHC!?cc`Ce0ZrO6c$@fS#mis90_Dy2{|gfdzU+l|C}{l~vwn_rX9}&&2mo$amNpOlM&sG*@jo$CnPPj>H5s*N;Nv`K?e~m)uSfaxg_#y0wVdLWYQ@AB_2^$Lg+dt01*gtNSo9?NmxIkV#=S%=HFc_<<!`R^xCI7K7Ro*@JwMAXof=0lB3G{C{)tY>PDWI2CXXeoT5QUp`SSbJ~b`hBWq*6f~AjCK%}>pzSFj2Kv8<5=ij"
)).decode("utf-8"))
_V17_MD_FRACTION = 2.0
_V17_ROOM_GUARD = True
_V17_FEED_GUARD = False
_V17_MD_ITEMS = ("MELON", "MILK", "STRAWBERRY", "WOOL")
_V17_MD_STATE = {
    0: {"last_step": -1, "target": False},
    1: {"last_step": -1, "target": False},
}
_V17_FEED_RESCUE_STATE = {
    0: {"last_step": -1, "day": -1, "active": {}},
    1: {"last_step": -1, "day": -1, "active": {}},
}
_V17_ROOM_EVAC_STATE = {
    0: {"last_step": -1, "day": -1, "active": None},
    1: {"last_step": -1, "day": -1, "active": None},
}


def _v17_md_signature(obs):
    seat = _seat(obs)
    farms = list(_get(obs, "farms", []) or [])
    opponent = farms[1 - seat] if len(farms) >= 2 else {}
    cows = sheep = 0
    for row in list(_get(opponent, "tiles", []) or []):
        for tile in list(row or []):
            if not isinstance(tile, dict):
                continue
            cows += int(tile.get("animal") == "COW")
            sheep += int(tile.get("animal") == "SHEEP")
    quadrants = len(_get(opponent, "unlocked_quadrants", []) or [])
    return cows, sheep, quadrants


def _v17_is_md_family(obs, step):
    seat = _seat(obs)
    state = _V17_MD_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {"last_step": step, "target": False}
        _V17_MD_STATE[seat] = state
    state["last_step"] = step
    if not state.get("target") and step >= 160:
        cows, sheep, quadrants = _v17_md_signature(obs)
        if (quadrants >= 2 and cows >= 4 and sheep <= 2) or cows >= 9:
            state["target"] = True
    return bool(state.get("target"))


def _v17_md_pickup_reserve(action, item):
    reserve = 0
    for order in [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]:
        if isinstance(order, (list, tuple)) and len(order) >= 2 and order[0] == "PICKUP" and order[1] == item:
            reserve += max(0, int(order[2])) if len(order) >= 3 else 1
    return reserve


def _v17_md_counter(obs, action, step):
    if _V17_MD_FRACTION <= 0 or not _v17_is_md_family(obs, step) or step + 1 >= len(_V17_MD_MARKETS):
        return action
    targets = {}
    for order in _V17_MD_MARKETS[step + 1]:
        if len(order) >= 3 and order[0] == "SELL" and order[1] in _V17_MD_ITEMS:
            targets[order[1]] = targets.get(order[1], 0) + max(0, int(order[2] or 0))
    if not targets:
        return action
    action = _copy_action(action)
    market = [list(order) for order in (action.get("market") or [])]
    shed = dict(_get(_get(obs, "private", {}) or {}, "shed", {}) or {})
    for item in _V17_MD_ITEMS:
        target = targets.get(item, 0)
        if target <= 0:
            continue
        existing_quantity = sum(
            max(0, int(order[2] or 0))
            for order in market
            if len(order) >= 3 and order[0] == "SELL" and order[1] == item
        )
        available = max(
            0,
            int(shed.get(item, 0) or 0)
            - existing_quantity
            - _v17_md_pickup_reserve(action, item),
        )
        quantity = min(available, max(1, int(round(target * _V17_MD_FRACTION))))
        if quantity <= 0:
            continue
        existing = next(
            (order for order in market if len(order) >= 3 and order[0] == "SELL" and order[1] == item),
            None,
        )
        if existing is not None:
            existing[2] = max(0, int(existing[2] or 0)) + quantity
        elif len(market) < 10:
            market.append(["SELL", item, quantity])
        else:
            continue
    action["market"] = market[:10]
    return action


def _v17_move_toward(position, target):
    x, y = int(position[0]), int(position[1])
    tx, ty = int(target[0]), int(target[1])
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    return ["PASS"]


def _v17_feed_guard(obs, action, step):
    hour = int(_get(obs, "hour", 0) or 0)
    day = int(_get(obs, "day", step // 24) or 0)
    if not _V17_FEED_GUARD or hour < 18:
        return action
    action = _align_hands(action, obs)
    seat = _seat(obs)
    state = _V17_FEED_RESCUE_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)) or day != int(state.get("day", -1)):
        state = {"last_step": step, "day": day, "active": {}}
        _V17_FEED_RESCUE_STATE[seat] = state
    state["last_step"] = step
    farm = _farm(obs, seat)
    private = _get(obs, "private", {}) or {}
    positions = [_get(farm, "farmer", [4, 4]), *list(_get(farm, "hands", []) or [])]
    inventories = list(_get(private, "inventories", []) or [])
    orders = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]

    threats = []
    for y, row in enumerate(list(_get(farm, "tiles", []) or [])):
        for x, tile in enumerate(list(row or [])):
            if (
                isinstance(tile, dict)
                and tile.get("animal")
                and int(tile.get("consecutive_unfed", 0) or 0) >= 1
                and not tile.get("fed_today", False)
            ):
                threats.append((x, y))
    threat_set = set(threats)
    active = state.setdefault("active", {})
    for actor, target in list(active.items()):
        actor = int(actor)
        if actor >= len(positions) or actor >= len(inventories) or tuple(target) not in threat_set:
            active.pop(actor, None)
            continue
        inventory = dict(inventories[actor] or {})
        if int(inventory.get("WHEAT", 0) or 0) <= 0:
            active.pop(actor, None)
            continue
        if tuple(positions[actor]) == tuple(target):
            orders[actor] = ["FEED"]
        else:
            orders[actor] = _v17_move_toward(positions[actor], target)

    claimed = {tuple(target) for target in active.values()}
    remaining_actions = max(1, 24 - hour)
    for target in threats:
        if target in claimed:
            continue
        if any(
            tuple(position) == target
            and actor < len(orders)
            and orders[actor]
            and orders[actor][0] == "FEED"
            for actor, position in enumerate(positions)
        ):
            continue
        candidates = []
        for actor, position in enumerate(positions):
            if actor in active or actor >= len(inventories):
                continue
            if int(dict(inventories[actor] or {}).get("WHEAT", 0) or 0) <= 0:
                continue
            distance = abs(int(position[0]) - target[0]) + abs(int(position[1]) - target[1])
            if distance + 1 <= remaining_actions:
                candidates.append((distance, actor))
        if not candidates:
            continue
        distance, actor = min(candidates)
        # Do not seize a worker early; start only at the last safe moment.
        if distance + 1 < remaining_actions:
            continue
        active[actor] = list(target)
        claimed.add(target)
        orders[actor] = ["FEED"] if distance == 0 else _v17_move_toward(positions[actor], target)
    action["farmer"] = orders[0] if orders else ["PASS"]
    action["hands"] = orders[1:]
    return action


def _v17_room_evac(obs, action, step):
    if not _V17_ROOM_GUARD or step < 648:
        return action
    hour = int(_get(obs, "hour", 0) or 0)
    day = int(_get(obs, "day", step // 24) or 0)
    seat = _seat(obs)
    state = _V17_ROOM_EVAC_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)) or day != int(state.get("day", -1)):
        state = {"last_step": step, "day": day, "active": None}
        _V17_ROOM_EVAC_STATE[seat] = state
    state["last_step"] = step
    if hour < 21:
        return action
    action = _align_hands(action, obs)
    farm = _farm(obs, seat)
    private = _get(obs, "private", {}) or {}
    positions = [_get(farm, "farmer", [4, 4]), *list(_get(farm, "hands", []) or [])]
    inventories = [dict(value or {}) for value in list(_get(private, "inventories", []) or [])]
    orders = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    shed = dict(_get(private, "shed", {}) or {})
    total = sum(max(0, int(value or 0)) for value in shed.values()) + sum(
        max(0, int(value or 0)) for inventory in inventories for value in inventory.values()
    )
    access = _shed_access(len(_get(farm, "tiles", []) or []) or 10)
    if hour == 21 and state.get("active") is None and total > 100:
        candidates = []
        for actor, (position, inventory) in enumerate(zip(positions, inventories)):
            saleable = sum(max(0, int(inventory.get(item, 0) or 0)) for item in _SELLABLE)
            if saleable <= 0 or actor >= len(orders) or (orders[actor] and orders[actor][0] != "PASS"):
                continue
            target = min(access, key=lambda point: abs(int(position[0]) - point[0]) + abs(int(position[1]) - point[1]))
            distance = abs(int(position[0]) - target[0]) + abs(int(position[1]) - target[1])
            if distance <= 2:
                candidates.append((distance, -saleable, actor, target))
        if candidates:
            _, _, actor, target = min(candidates)
            state["active"] = {"actor": actor, "target": list(target)}
    active = state.get("active")
    if active is None:
        return action
    actor = int(active["actor"])
    target = tuple(active["target"])
    if actor >= len(positions) or actor >= len(inventories):
        state["active"] = None
        return action
    if tuple(positions[actor]) != target:
        orders[actor] = _v17_move_toward(positions[actor], target)
    elif hour == 23:
        orders[actor] = ["DROP"]
        market = [list(order) for order in (action.get("market") or [])]
        existing_sales = {}
        for order in market:
            if len(order) >= 3 and order[0] == "SELL":
                existing_sales[order[1]] = existing_sales.get(order[1], 0) + max(0, int(order[2] or 0))
        needed = max(0, total - 100)
        priority = ("WOOL", "MILK", "EGG", "MELON", "STRAWBERRY", "TOMATO", "CARROT", "FERTILIZER", "WHEAT")
        inventory = inventories[actor]
        for item in priority:
            available = max(0, int(inventory.get(item, 0) or 0) - existing_sales.get(item, 0))
            quantity = min(needed, available)
            if quantity <= 0:
                continue
            existing = next(
                (order for order in market if len(order) >= 3 and order[0] == "SELL" and order[1] == item),
                None,
            )
            if existing is not None:
                existing[2] = int(existing[2] or 0) + quantity
            elif len(market) < 10:
                market.append(["SELL", item, quantity])
            else:
                continue
            needed -= quantity
            if needed <= 0:
                break
        action["market"] = market[:10]
    action["farmer"] = orders[0] if orders else ["PASS"]
    action["hands"] = orders[1:]
    return action


def _v17_room_guard(obs, action, step):
    if not _V17_ROOM_GUARD or step % 24 != 23:
        return action
    action = _copy_action(action)
    private = _get(obs, "private", {}) or {}
    shed = {key: max(0, int(value or 0)) for key, value in dict(_get(private, "shed", {}) or {}).items()}
    inventories = [dict(value or {}) for value in list(_get(private, "inventories", []) or [])]
    carried = sum(max(0, int(value or 0)) for inventory in inventories for value in inventory.values())
    farm = _farm(obs, _seat(obs))
    positions = [_get(farm, "farmer", [4, 4]), *list(_get(farm, "hands", []) or [])]
    orders = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    produced = consumed = 0
    for actor, order in enumerate(orders):
        if actor >= len(positions) or not isinstance(order, list) or not order:
            continue
        tile = _tile_at(farm, positions[actor])
        if order[0] == "HARVEST" and isinstance(tile, dict):
            produced += max(0, int(tile.get("yield_units", 0) or 0))
        elif order[0] == "COLLECT_FERTILIZER" and isinstance(tile, dict) and tile.get("fertilizer_available", False):
            produced += 1
        elif order[0] in ("FEED", "FERTILIZE"):
            consumed += 1
        elif order[0] == "PLACE" and len(order) >= 2 and order[1] in ("GOOSE", "COW", "SHEEP"):
            consumed += 1
    market = [list(order) for order in (action.get("market") or [])]
    planned_sells = {}
    planned_buys = 0
    for order in market:
        if len(order) < 3:
            continue
        quantity = max(0, int(order[2] or 0))
        if order[0] == "SELL":
            planned_sells[order[1]] = planned_sells.get(order[1], 0) + quantity
        elif order[0] in ("BUY_PRODUCT", "BUY_ANIMAL"):
            planned_buys += quantity
    actual_existing_sells = sum(min(shed.get(item, 0), quantity) for item, quantity in planned_sells.items())
    needed = max(
        0,
        sum(shed.values()) + carried + produced - consumed + planned_buys - actual_existing_sells - 100,
    )
    if needed <= 0:
        return action
    # Finished animal products and sale-only crops are safest to liquidate.
    priority = ("WOOL", "MILK", "EGG", "MELON", "STRAWBERRY", "TOMATO", "CARROT", "FERTILIZER", "WHEAT")
    for item in priority:
        already = planned_sells.get(item, 0)
        available = max(0, shed.get(item, 0) - already)
        quantity = min(needed, available)
        if quantity <= 0:
            continue
        existing = next(
            (order for order in market if len(order) >= 3 and order[0] == "SELL" and order[1] == item),
            None,
        )
        if existing is not None:
            existing[2] = int(existing[2] or 0) + quantity
        elif len(market) < 10:
            market.append(["SELL", item, quantity])
        else:
            continue
        planned_sells[item] = already + quantity
        needed -= quantity
        if needed <= 0:
            break
    action["market"] = market[:10]
    return action

def agent(obs):
    try:
        actions = _kawa_actions(obs)
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)
        action = _weed_repair_action(obs, _copy_action(actions[step]), step)
        action = _v17_feed_guard(obs, action, step)
        action = _v17_room_evac(obs, action, step)
        action = _repay_shift(obs, action, step)
        action = _rank_sell_slots(obs, action, None)
        action = _preempt_shift(obs, action, step)
        action = _v17_r5_counter(obs, action, step)
        action = _v17_md_counter(obs, action, step)
        action = _v17_room_guard(obs, action, step)
        action = _terminal_liquidation(obs, action, step)
        return _align_hands(action, obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
            "market": [],
        }

def _kaggle_submission_entrypoint(obs):
    return agent(obs)
