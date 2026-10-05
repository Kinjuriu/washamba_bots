_Ab='COLLECT_FERTILIZER'
_Aa='lead_debts'
_AZ='BUILD_PASTURE'
_AY='placed_day'
_AX='initial'
_AW='last_step'
_AV='quantity'
_AU='water'
_AT='birth'
_AS='hinge'
_AR='projected'
_AQ='S2C_ok'
_AP='BRUNCH_SPOT'
_AO='saved'
_AN='FEED'
_AM='loaded'
_AL='hires_today'
_AK='FERTILIZE'
_AJ='watered_today'
_AI='SMOOTHIE_SHOP'
_AH='ICE_CREAM_SHOP'
_AG='fed_today'
_AF='committed'
_AE='first'
_AD='harvest'
_AC='fertilized_until_day'
_AB='BUY_LAND'
_AA='money'
_A9='linear'
_A8='log'
_A7='YARN_STORE'
_A6='T11'
_A5='WATER'
_A4='DROP'
_A3='planted_day'
_A2='PIZZA_SHOP'
_A1='path'
_A0='day'
_z='unlocked_quadrants'
_y='sqrt'
_x='unlocked_shops'
_w='town'
_v='FARMERS_MARKET'
_u='MELON'
_t='BUY_SEED'
_s='BUY_ANIMAL'
_r='NORTH'
_q='SOUTH'
_p='WEST'
_o='EAST'
_n='workers'
_m='inventory'
_l='HARVEST'
_k='kind'
_j='yield_units'
_i='GOOSE'
_h='pending'
_g='PLANT'
_f='COW'
_e='STRAWBERRY'
_d='PLACE'
_c='SHEEP'
_b='EGG'
_a='PICKUP'
_Z='shed'
_Y='WOOL'
_X='MILK'
_W='HIRE'
_V='prices'
_U='crop'
_T='animal'
_S='BUY_PRODUCT'
_R='inventories'
_Q='player'
_P='CARROT'
_O='farms'
_N='private'
_M='tiles'
_L='TOMATO'
_K='step'
_J='PASS'
_I='FERTILIZER'
_H='farmer'
_G='SELL'
_F=True
_E=False
_D='WHEAT'
_C='hands'
_B=None
_A='market'
from mirror_plan import TAPE
PRODUCTS=_D,_P,_L,_e,_u,_b,_X,_Y,_I
HARVESTED=_e,_X,_Y,_b,_u,_P,_L
YARN7=1
YARN10=1
YARN6=2
MILK_S2C=2
YARN_FIRST=_E
YARN_FIRST_NOMILK=_F
S2C_PRICE=_F
DAY6=range(144,168)
DAY7=range(168,192)
DAY10_11=range(240,288)
S2C_WINDOW=range(216,264)
MILK_SHOPS=_A2,_AH,_AI
LEAD=8
T11=_E
T11_EXTRA=60
T11_MAXS=0
T11_TMIN=0
T11_TMAX=3
TOMATO_SHOPS_T11=_A2,_v
T11_DELIVER=_F
STRAW_SHOPS=_AP,_AH,_AI,_v
NO_GARDEN_ROUTED=_E
NO_S2C_ROUTED=_E
NO_T11_ROUTED=_E
_GARDEN=[_B]
D29=9
D29_DEADLINE=718
D29_NEAREST=_F
D29_GATE='garden'
def _d29_on():
	if not D29:return _E
	if D29_GATE=='garden':A=_GARDEN[0];return A is not _B and getattr(A,'decided',_E)and not getattr(A,'blocked',_E)
	return _F
D29_WIN={_D:(2,4,6),_P:(2,3,4),_u:(10,12,6)}
D29_PROD={_f:_X,_c:_Y,_i:_b}
def _d29_toward(p,q):
	if q[0]!=p[0]:return[_o if q[0]>p[0]else _p]
	if q[1]!=p[1]:return[_q if q[1]>p[1]else _r]
	return[_J]
def _d29_route(out,obs,step):
	U=step;N=obs;J=out;O=N[_O][N[_Q]];b=O[_M];V=len(b);B=V//2;c=U//24;d=(B-1,B-1),(B,B-1),(B-1,B),(B,B);W=(N.get(_A)or{}).get(_V)or{};P=min(D29,len(O[_C]));j=[tuple(O[_H])]+[tuple(A)for A in O[_C][:P]];e=N[_N][_R];H={}
	for K in range(V):
		for L in range(V):
			if L>=B and K>=B:continue
			C=b[K][L]
			if not isinstance(C,dict):continue
			if C.get(_k)==_g:
				Q=C.get(_U);R=C.get(_j,0)
				if Q in D29_WIN:
					k,X,l=D29_WIN[Q];Y=c-C.get(_A3,c)
					if Y<k:continue
					S=(X+1)//2<=Y<=X and not C.get(_AJ)and R<l;f=R+(1 if S else 0)
					if f<=0:continue
					m=2 if Y>X else 1;H[L,K]=m*f*max(1,W.get(Q,30)),S
				elif R>=1:H[L,K]=R*max(1,W.get(Q,60)),_E
			elif C.get(_T)and C.get(_j,0)>=1:H[L,K]=C[_j]*max(1,W.get(D29_PROD.get(C[_T]),40)),_E
	F=_ST.setdefault('d29_assign',{})
	for A in list(F):
		if F[A]not in H or A>P:del F[A]
	E=[J[_H]]+list(J[_C]);E+=[[_J]]*(P+1-len(E))
	for(A,D)in enumerate(j):
		n=e[A]if A<len(e)else{};g=sum(B for(A,B)in n.items()if A in PRODUCTS);T=min(d,key=lambda a:abs(a[0]-D[0])+abs(a[1]-D[1]));Z=abs(T[0]-D[0])+abs(T[1]-D[1])
		if g and U+Z>=D29_DEADLINE:E[A]=[_A4]if Z==0 else _d29_toward(D,T);F.pop(A,_B);continue
		G=F.get(A)
		if G is _B:
			o=set(C for(B,C)in F.items()if B!=A);M=_B
			for(I,(h,S))in H.items():
				if I in o:continue
				a=abs(I[0]-D[0])+abs(I[1]-D[1]);p=min(abs(I[0]-A[0])+abs(I[1]-A[1])for A in d)
				if U+a+(2 if S else 1)+p>D29_DEADLINE:continue
				i=(-a,h)if D29_NEAREST else(h/(a+1.),)
				if M is _B or i>M[0]:M=i,I
			if M:G=M[1];F[A]=G
		if G is not _B:
			if G==D:E[A]=[_A5]if H[G][1]else[_l]
			else:E[A]=_d29_toward(D,G)
		elif g:E[A]=[_A4]if Z==0 else _d29_toward(D,T)
		else:E[A]=[_J]
	J[_H]=E[0];J[_C]=E[1:P+1];return J
NONMIRROR_LEAD=4
ADAPT_LEAD=_F
_RETURNING=set()
_ST={}
_CUR={}
def _t11_on(obs,f):
	if not T11:return _E
	if _A6 not in _ST:
		if f<264:return _E
		_ST[_A6]=sum(1 for A in _shops(obs)[:3]if A in STRAW_SHOPS)<=T11_MAXS and T11_TMIN<=sum(1 for A in _shops(obs)[:3]if A in TOMATO_SHOPS_T11)<=T11_TMAX
		if _ST[_A6]and _GARDEN[0]is not _B:_GARDEN[0].min_deficit=_GARDEN[0].min_deficit+T11_EXTRA
	return _ST[_A6]
def _t11_post(out,obs,step):
	R='T11_tiles';G=obs;B=out
	if not(T11 and _ST.get(_A6)):return B
	H=step//24;L=G[_O][G[_Q]];M=L[_M]
	if 12<=H<=21:
		N=_ST.setdefault(R,set())
		for(I,S)in enumerate(M):
			for(J,A)in enumerate(S):
				if isinstance(A,dict)and A.get(_U)==_L and A.get(_A3)==11:N.add((J,I))
	if 19<=H<=27:
		N=_ST.get(R,set());F=[B[_H]]+list(B[_C]);K=[L[_H]]+list(L[_C]);P=G[_N][_R];D=len(M)//2;T=(D-1,D-1),(D,D-1),(D-1,D),(D,D)
		for(C,E)in enumerate(F):
			O=P[C]if C<len(P)else{}
			if C<len(K)and E and O.get(_L,0)>0 and tuple(K[C])in T and T11_DELIVER:
				if E[0]==_J or E[0]==_d and len(E)>1 and E[1]!=_L and O.get(E[1],0)<=0:F[C]=[_d,_L,O[_L]];continue
			if C>=len(K)or not E or E[0]not in(_A5,_AK,_l,_J,_g,'DIG'):continue
			J,I=K[C]
			if(J,I)not in N:continue
			A=M[I][J]
			if isinstance(A,dict)and A.get(_k)==_g and A.get(_U)==_L:
				Q=A.get(_j,0)
				if Q>=3 or Q>=1 and H>=22:F[C]=[_l]
			elif isinstance(A,dict)and A.get(_k)=='WEED'and H>=23:F[C]=['DIG']
		B[_H]=F[0];B[_C]=F[1:]
	if G[_N][_Z].get(_L,0)>0 and not any(A and A[0]==_G and A[1]==_L for A in B[_A]):B[_A]=([[_G,_L,999]]+[A for A in B[_A]if A])[:10]
	return B
def _shops(obs):return(obs.get(_w)or{}).get(_x)or[]
def _yarn(obs,k):return sum(1 for A in _shops(obs)[:k]if A==_A7)
def _milk(obs,k):return sum(1 for A in _shops(obs)[:k]if A in MILK_SHOPS)
def _sub_unit(u,swap):
	A=swap
	if not u:return u
	u=list(u)
	if u[0]in(_a,_d)and len(u)>1 and u[1]in A:u[1]=A[u[1]]
	if u[0]=='BUILD_COOP'and _i in A:u[0]=_AZ
	return u
def plan(obs,step,flags_of=_B):
	I=flags_of;D=obs;C=step;F=C if I is _B else I;G=TAPE[min(C,len(TAPE)-1)]or{};J=F>=144 and(_yarn(D,2)>=YARN6 or YARN_FIRST and _shops(D)[:1]==[_A7]and not(YARN_FIRST_NOMILK and len(_shops(D))>1 and _shops(D)[1]in MILK_SHOPS));K=F>=168 and _yarn(D,2)>=YARN7;H=F>=240 and _yarn(D,3)>=YARN10;L=F>=216 and not(NO_S2C_ROUTED and TAPE.route is not _B)and _yarn(D,3)==0 and _milk(D,3)>=MILK_S2C and(not S2C_PRICE or _ST.get(_AQ,_E));E={}
	if J and C in DAY6:E[_f]=_c
	if K and C in DAY7:E[_f]=_c
	if H and C in DAY10_11:E[_i]=_c
	if L and C in S2C_WINDOW:E[_c]=_f
	A={_H:list(G.get(_H)or[_J]),_C:[list(A)for A in G.get(_C)or[]],_A:[]}
	if E:A[_H]=_sub_unit(A[_H],E);A[_C]=[_sub_unit(A,E)for A in A[_C]]
	M=J or K or H
	for B in G.get(_A)or[]:
		if not B:continue
		B=list(B)
		if B[0]==_s and B[1]in E:B[1]=E[B[1]]
		elif B[0]==_G:
			if B[1]==_b and H:B=[_G,_Y,999]
			elif B[1]==_Y and M:B=[_G,_Y,999]
			elif B[1]==_X and L:B=[_G,_X,999]
		A[_A].append(B)
	if D29 and C>=696 and _d29_on():A[_A]=[A for A in A[_A]if A[0]not in(_W,_S,_t)]+([[_W]]*min(D29,7)if C==696 else[[_W]]*max(0,D29-7)if C==697 else[]);A[_H]=[_J];A[_C]=[[_J]]*(min(D29,7)if C==697 else D29 if C>697 else 0)
	if 264<=C<288 and not(NO_T11_ROUTED and TAPE.route is not _B)and _t11_on(D,F):A[_H]=[_g,_L]if A[_H][:2]==[_g,_e]else A[_H];A[_C]=[[_g,_L]if A[:2]==[_g,_e]else A for A in A[_C]];A[_A]=[[_t,_L,A[2]]if A[0]==_t and A[1]==_e else A for A in A[_A]]
	return A
def _base_agent(obs,config):
	U='fam';T='sim';A=obs;global _RETURNING;B=int(A[_K])
	if B==0:_RETURNING=set();_ST.clear()
	_CUR['obs']=A;_CUR[_K]=B
	if S2C_PRICE and B>=216 and _AQ not in _ST and _yarn(A,3)==0 and _milk(A,3)>=MILK_S2C:O=(A.get(_A)or{}).get(_V)or{};_ST[_AQ]=int(O.get(_X,0))>=int(O.get(_Y,0))
	C=plan(A,B)
	if D29 and B>=696 and _d29_on():C=_d29_route(C,A,B)
	if B<712:
		P=lambda t:plan(A,t,flags_of=B)
		if NONMIRROR_LEAD is not _B and B%24==0:_ST[T]=board_similarity_robust(A);_ST[U]=_ST[T]>=.7 or B<48
		if NONMIRROR_LEAD is not _B and not _ST.get(U,_F):Q=NONMIRROR_LEAD
		else:Q=rival_lead_horizon(A,_ST,P,B,LEAD,gated=_F,strict=_F,window=17)if ADAPT_LEAD else LEAD
		C=lead_layer(C,A,P,_ST,B,Q,block=_F,min_price=2,last=695,first=0,fert=LEAD_FERT)
		if ADAPT_LEAD:_ST['rlt_prev']=dict(step=B,inv=dict(A[_A][_m]),prices=dict((A.get(_A)or{}).get(_V)or{}),proj=projected_shed(A,C))
		C=order_rows(C,A,sales_first=_F,quote=_AR);C=_t11_post(C,A,B);return C
	K=A[_O][A[_Q]];D=len(K[_M])//2;V=(D-1,D-1),(D,D-1),(D-1,D),(D,D);R=[K[_H]]+K[_C];S=A[_N][_R];E=[C[_H]]+C[_C];E=[E[A]if A<len(E)else[_J]for A in range(len(R))]
	for(F,W)in enumerate(R):
		X=S[F]if F<len(S)else{};L={A:B for(A,B)in X.items()if A in PRODUCTS and B>0};Y=bool(L)and set(L)=={_I}
		if Y:
			H,I=W;M,N=min(V,key=lambda p:abs(p[0]-H)+abs(p[1]-I));Z=abs(M-H)+abs(N-I)
			if Z+1<=719-B:_RETURNING.add(F);E[F]=[_o if M>H else _p]if M!=H else[_q if N>I else _r]if N!=I else[_A4]
		elif F in _RETURNING and not L:E[F]=[_J]
	G=[]
	for J in(TAPE[min(B,len(TAPE)-1)]or{}).get(_A)or[]:
		if J and J[0]==_G and J[1]not in G:G.append(J[1])
	G.extend(A for A in PRODUCTS if A not in G);C.update(farmer=E[0],hands=E[1:],market=[[_G,A,999]for A in G]);return C
MARKET_PARAMS={_D:(25,400,_y,.8,_A8,.2),_P:(35,450,_AS,1.,_y,.7),_L:(60,200,_AS,.4,_y,.6),_e:(120,100,_y,.7,_A9,1.6),_u:(250,300,_A8,.2,'sq',3.6),_b:(50,332,_AS,.4,_A8,.2),_X:(160,122,_y,.6,_A9,1.6),_Y:(200,105,_A8,.2,'sq',3.2),_I:(100,200,_A9,.4,_A9,.4)}
ANIMAL_ITEMS=_i,_f,_c
ACCESS=(4,4),(5,4),(4,5),(5,5)
def _shape(f,x,T):
	import math as A;x=max(.0,x)
	if f==_A9:return x
	if f=='sq':return x*x
	if f==_y:return A.sqrt(x)
	if f==_A8:return A.log(1.+x)
	B=x/T;return B+8.*max(.0,B-1.)**2
def market_price(item,inventory):
	C=inventory;B,A,D,G,E,H=MARKET_PARAMS[item]
	if C<10000:F=B+G*B/_shape(D,A,A)*_shape(D,10000-C,A)
	else:F=B-H*B/_shape(E,A,A)*_shape(E,C-10000,A)
	return max(1,int(round(F)))
def projected_shed(obs,out):
	D=obs;F=D[_O][D[_Q]];G=[tuple(F[_H])]+[tuple(A)for A in F[_C]];H=D[_N][_R];B=dict(D[_N][_Z]);K=[out.get(_H)or[_J]]+list(out.get(_C)or[])
	for(E,A)in enumerate(K[:len(G)]):
		if not A or G[E]not in ACCESS:continue
		I=H[E]if E<len(H)else{}
		if A[0]==_A4:
			for(J,C)in I.items():B[J]=B.get(J,0)+max(0,int(C))
		elif A[0]==_d and len(A)>1 and A[1]not in ANIMAL_ITEMS:C=int(A[2])if len(A)>2 else 1;B[A[1]]=B.get(A[1],0)+min(C,max(0,int(I.get(A[1],0))))
		elif A[0]==_a and len(A)>1:C=int(A[2])if len(A)>2 else 1;B[A[1]]=max(0,B.get(A[1],0)-C)
	return B
def lead_layer(out,obs,plan_at,st,step,horizon,block=_F,min_price=2,last=695,first=0,fert=_E):
	J=last;D=step;C=out;H=st.setdefault(_Aa,{});K=H.pop(D,{});E=[]
	for A in C[_A]:
		if A and A[0]==_G and len(A)>2 and K.get(A[1],0)>0:
			F=int(A[2]);Q=min(F,K[A[1]]);K[A[1]]-=Q;F-=Q
			if F<=0:continue
			A=[_G,A[1],F]
		E.append(A)
	C[_A]=E
	if D<first or D>J or D>=712:return C
	R=min(J,D+horizon,(D//72+1)*72-1 if block else J)
	if R<=D:return C
	U=projected_shed(obs,C);V=(obs.get(_A)or{}).get(_V)or{};L={}
	for A in E:
		if A and A[0]==_G and len(A)>2:L[A[1]]=L.get(A[1],0)+int(A[2])
	W={A[1]for A in E if A and A[0]==_S};X={A[1]for A in[C.get(_H)or[]]+list(C.get(_C)or[])if A and A[0]==_a and len(A)>1};Y=HARVESTED+((_I,)if fert and D%24>=6 else())
	for B in Y:
		if B in W or B in X or V.get(B,0)<min_price:continue
		I=max(0,U.get(B,0)-L.get(B,0))
		if I<=0:continue
		M=[]
		for G in range(D+1,R+1):
			N=plan_at(G)or{};Z=[N.get(_H)or[]]+list(N.get(_C)or[])
			if any(A and A[0]==_a and len(A)>1 and A[1]==B for A in Z):break
			S=[A for A in N.get(_A)or[]if A]
			if any(A[0]==_S and A[1]==B for A in S):break
			a=sum(int(A[2])for A in S if A[0]==_G and len(A)>2 and A[1]==B);O=min(I,max(0,a-H.get(G,{}).get(B,0)))
			if O:M.append((G,O));I-=O
			if I<=0:break
		P=sum(A for(B,A)in M)
		if not P:continue
		T=_E
		for A in E:
			if A and A[0]==_G and len(A)>2 and A[1]==B:A[2]=int(A[2])+P;T=_F;break
		if not T:
			if len(E)>=10:continue
			E.append([_G,B,P])
		for(G,F)in M:H.setdefault(G,{})[B]=H.get(G,{}).get(B,0)+F
	C[_A]=E;return C
def board_similarity(obs):
	D=obs[_O];E=obs[_Q];F,G=D[E],D[1-E]
	if list(F.get(_z)or[])!=list(G.get(_z)or[]):return .0
	H=A=0
	for(B,C)in zip([B for A in F[_M]for B in A],[B for A in G[_M]for B in A]):
		I=(B.get(_U),B.get(_T))if isinstance(B,dict)else(_B,_B);J=(C.get(_U),C.get(_T))if isinstance(C,dict)else(_B,_B)
		if I!=(_B,_B)or J!=(_B,_B):A+=1;H+=I==J
	return H/A if A>=8 else .0
def board_similarity_robust(obs):
	D=obs[_O];E=obs[_Q];I,J=D[E],D[1-E];F=A=0
	for(B,C)in zip([B for A in I[_M]for B in A],[B for A in J[_M]for B in A]):
		G=(B.get(_U),B.get(_T))if isinstance(B,dict)else(_B,_B);H=(C.get(_U),C.get(_T))if isinstance(C,dict)else(_B,_B)
		if G!=(_B,_B)or H!=(_B,_B):A+=1;F+=G==H
	return F/A if A>=8 else .0
RLT_ITEMS=_e,_X,_b,_u,_P
def rival_lead_horizon(obs,st,plan_at,step,base,cap=20,window=24,min_units=2,gated=_F,first=288,last=696,strict=_E):
	S='rlt_fam';P=gated;I=base;H=obs;C=st;A=step;D=C.get('rlt_prev');J=C.setdefault('rlt_obs',[])
	if P and A%24==0:C[S]=board_similarity(H)>=.9
	if D and D[_K]==A-1 and(A-1)%4!=0 and(A-1)%24!=23 and first<=A-1<last and(C.get(S)or not P):
		T=H[_A][_m];Q=H[_N][_Z];U=C.get(_Aa,{})
		for B in RLT_ITEMS:
			R=max(0,D['proj'].get(B,0)-Q.get(B,0));F=int(T[B])-int(D['inv'][B])-(R if D[_V].get(B,0)>1 else 0)
			if F<min_units or R>0 or Q.get(B,0)<=0:continue
			K=0;L=_B
			for M in range(A,min(A-1+window,711)+1):
				V=[A for A in(plan_at(M)or{}).get(_A)or[]if A];G=sum(int(A[2])for A in V if A[0]==_G and len(A)>2 and A[1]==B)
				if not G:continue
				if K==0 and(U.get(M,{}).get(B,0)>=G or F<G-1):break
				K+=G
				if K<=F+1:L=M-(A-1)
				else:break
			if L is not _B:J.append((A-1,B,F,L))
	if len(J)<2:return I
	E=sorted((A[3]for A in J),reverse=_F);N=_B if strict else E[1]
	for O in range(len(E)-1):
		if E[O]-E[O+1]<=1:N=E[O];break
	if N is _B:return I
	return max(I,min(cap,N+1))
SHOPS_OF={_e:(_AP,_AH,_AI,_v),_X:(_A2,_AH,_AI),_Y:(_A7,),_b:('BAKERY',_AP),_P:('PET_CAFE',_v),_L:(_A2,_v)}
HOLD_PRICE={_e:60,_X:80,_Y:100,_b:25}
def hold_floor(out,obs,step,room=85,prices_at=HOLD_PRICE):
	D=prices_at;C=obs;B=out
	if step>=712:return B
	F=set((C.get(_w)or{}).get(_x)or[]);G=(C.get(_A)or{}).get(_V)or{};H=C[_N][_Z];I=sum(H.values());E=[]
	for A in B[_A]:
		if A and A[0]==_G and len(A)>2 and A[1]in D and not F&set(SHOPS_OF[A[1]])and G.get(A[1],0)<D[A[1]]and I<room:continue
		E.append(A)
	B[_A]=E;return B
def exposure(obs,item,qty,batch=8):A=item;B=obs[_A][_m][A];return sum(market_price(A,B+C)for C in range(qty))-sum(market_price(A,B+batch+C)for C in range(qty))
def order_rows(out,obs,sales_first=_F,quote=_F,hygiene=_E):
	J=quote;H=obs;F=out;A=[list(A)for A in F[_A]if A]
	if hygiene:
		E=[];G={}
		for D in A:
			if D[0]==_G and len(D)>2:
				if int(D[2])<=0:continue
				if D[1]in G:E[G[D[1]]][2]=int(E[G[D[1]]][2])+int(D[2]);continue
				G[D[1]]=len(E)
			E.append(D)
		A=E
	if sales_first:
		for C in range(len(A)):
			if A[C][0]!=_G:continue
			B=C
			while B>0 and A[B-1][0]!=_G and not(A[B-1][0]in(_S,_s)and A[B-1][1]==A[B][1]):A[B-1],A[B]=A[B],A[B-1];B-=1
	if J:
		K=projected_shed(H,F)if J==_AR else H[_N][_Z];C=0
		while C<len(A):
			if A[C][0]!=_G:C+=1;continue
			B=C
			while B<len(A)and A[B][0]==_G:B+=1
			I=A[C:B]
			if len({A[1]for A in I})==len(I):A[C:B]=sorted(I,key=lambda r:-exposure(H,r[1],min(int(r[2]),K.get(r[1],0)))if r[1]in MARKET_PARAMS else 0)
			C=B
	F[_A]=A;return F
HALF=5
ACCESS=(HALF-1,HALF-1),(HALF,HALF-1),(HALF-1,HALF),(HALF,HALF)
SE_TILES=sorted([(A,B)for A in range(HALF,2*HALF)for B in range(HALF,2*HALF)if(A,B)!=(HALF,HALF)],key=lambda p:(abs(p[0]-HALF)+abs(p[1]-HALF),p[1],p[0]))
TOMATO_SHOPS=_A2,_v
def _toward(pos,tgt):
	A,B=pos;C,D=tgt
	if C!=A:return[_o if C>A else _p]
	if D!=B:return[_q if D>B else _r]
	return[_J]
def _nearest_access(pos):return min(ACCESS,key=lambda p:abs(p[0]-pos[0])+abs(p[1]-pos[1]))
def deficit_by(shops,day=27):return day+sum(6*max(0,day-(3*(A+1)-1))for(A,B)in enumerate(shops)if B in TOMATO_SHOPS)
def clusters(tiles,k):
	B=sorted(tiles);E=len(B);C=[];A=0
	for F in range(max(1,k)):D=A+(E-A)//(max(1,k)-F);C.append(B[A:D]);A=D
	return C
class SETomato7:
	def __init__(A,base,plant_day=18,hire_hour=2,min_deficit=300,big=450,big_opp=400,small=(12,3),large=(16,4),early=(2,1),last_step=717,fixed=_B,harvest_at=3,lean_offsets=()):C=small;B=plant_day;A.lean_offsets=set(lean_offsets);A.base=base;A.plant_day=B;A.hire_hour=hire_hour;A.min_deficit=min_deficit;A.big=big;A.big_opp=big_opp;A.small=C;A.large=large;A.early=early;A.fixed=fixed;A.prod_days=set(range(B+7,B+11));A.fert_days={B+7,B+10};A.last_plant_day=B+1;A.last_day=B+11;A.last_step=last_step if B+11>=29 else(B+12)*24-2;A.harvest_at=harvest_at;A.tiles=SE_TILES[:C[0]];A.late_crew=C[1];A.groups=clusters(A.tiles,1);A.n_before=_B;A.day_seen=-1;A.k_today=0;A.decided=_E
	def crew(A,day):
		B=day
		if B<A.plant_day or B>min(29,A.last_day):return 0
		if B==A.plant_day:return A.early[0]
		if B<A.plant_day+7:return A.early[1]
		if B-A.plant_day in A.lean_offsets:return max(1,A.late_crew-1)
		return A.late_crew
	def __call__(A,obs):
		B=obs;D=A.base(B);N=B[_Q];G=B[_O][N];V=int(B[_K]);C=int(B[_A0]);F=int(B['hour']);I=G[_C];O=B[_N][_R];P=B[_N][_Z];W=B[_N]['seeds'];J=G.get(_z)or[]
		if C!=A.day_seen:A.day_seen=C;A.n_before=_B
		K=[list(A)for A in D.get(_A)or[]if A];E=[];Q=(B.get(_w)or{}).get(_x)or[]
		if getattr(A,'blocked',_E):return D
		if C==A.plant_day and F==1 and'SE'not in J and G[_AA]>=5500 and deficit_by(Q,27)>=A.min_deficit:E.append([_AB]);E.append([_t,_L,A.small[0]+2])
		if'SE'in J and C==A.plant_day and F==A.hire_hour and not A.decided:
			A.decided=_F
			if A.fixed:H,R=A.fixed
			else:X=B[_O][1-N];Y=len(X.get(_z)or[])>=4;S=deficit_by(Q,27);H,R=A.large if S>=A.big or Y and S>=A.big_opp else A.small
			A.tiles=SE_TILES[:H];A.late_crew=R
			if H>A.small[0]:E.append([_t,_L,H-A.small[0]])
		if'SE'in J and A.decided and F==A.hire_hour and A.crew(C)>0:
			A.k_today=A.crew(C);A.n_before=len(I);E.extend([[_W]]*A.k_today)
			if C in A.fert_days:E.append([_S,_I,len(A.tiles)])
		L=[]
		if A.n_before is not _B and F>A.hire_hour:
			T=max(0,min(len(I)-A.n_before,A.k_today));A.groups=clusters(A.tiles,T);Z=(list(D.get(_C)or[])+[[_J]]*A.n_before)[:A.n_before]
			for U in range(T):M=A.n_before+U;a=tuple(I[M]);b=O[M+1]if M+1<len(O)else{};L.append(A._decide(U,a,b,G,W,P,C,F,V))
			D[_C]=Z+L
		c=any(A and A[0]==_d and A[1]==_L for A in L)
		if c or P.get(_L,0)>0:K=[[_G,_L,999]]+[A for A in K if not(A[0]==_G and A[1]==_L)]
		D[_A]=(K+E)[:10];return D
	def _decide(A,j,pos,inv,farm,seeds,shed,day,hour,step):
		Y='consecutive_unwatered';O=step;N=hour;M=shed;I=farm;H=pos;F=day;P=A.groups[j]if j<len(A.groups)else[];S,T=H;J=inv.get(_L,0);L=inv.get(_I,0);Q=100-sum(M.values());K=_nearest_access(H);U=abs(K[0]-S)+abs(K[1]-T);Z=F>=min(29,A.last_day)
		def R():
			if H in ACCESS:return[_d,_L,min(J,Q)]if Q>=1 else[_J]
			return _toward(H,K)
		if J and O+U+1>=A.last_step:return R()
		if J and(J>=12 or N+U>=22):return R()
		if F in A.fert_days and L==0 and H in ACCESS and N<=A.hire_hour+2 and M.get(_I,0)>0:
			V=sum(1 for(A,B)in P if isinstance(I[_M][B][A],dict)and I[_M][B][A].get(_k)==_g and I[_M][B][A].get(_AC,-1)<F)
			if V:return[_a,_I,min(V,M[_I])]
		if L and H in ACCESS and not any(isinstance(I[_M][B][A],dict)and I[_M][B][A].get(_AC,-1)<F for(A,B)in P):return[_d,_I,L]if Q>=1 else[_J]
		G=[]
		for(D,E)in P:
			B=I[_M][E][D];C=abs(D-S)+abs(E-T)
			if B=='LOCKED':continue
			if isinstance(B,dict)and B.get(_k)==_g:
				W=B.get(_j,0);X=abs(K[0]-D)+abs(K[1]-E);a=N+C+1+X<=22 or O>=A.last_step-20
				if Z:
					if W>=1 and O+C+1+X+1<A.last_step:G.append((.5,C,(D,E),[_l]))
					continue
				if not B.get(_AJ,_E)and B.get(Y,0)>=1:G.append((0,C,(D,E),[_A5]))
				if W>=A.harvest_at and a:G.append((.5,C,(D,E),[_l]))
				if L>0 and F in A.fert_days and B.get(_AC,-1)<F:G.append((1.,C,(D,E),[_AK]))
				if not B.get(_AJ,_E)and B.get(Y,0)==0:G.append((1.1 if F in A.prod_days else 4,C,(D,E),[_A5]))
			elif isinstance(B,dict)and B.get(_k)=='WEED':
				if F<=A.last_plant_day:G.append((3,C,(D,E),['DIG']))
			elif B is _B:
				if seeds.get(_L,0)>0 and F<=A.last_plant_day:G.append((2,C,(D,E),[_g,_L]))
		if not G:return R()if J else[_J]
		d,C,b,c=min(G);return c if C==0 else _toward(H,b)
CROPS={_D:(2,4,6),_P:(2,3,4)}
MOVES={_r:(0,-1),_q:(0,1),_o:(1,0),_p:(-1,0)}
def _fib(n):
	A,B=1,1
	for C in range(n):A,B=B,A+B
	return A
def _walk(pos,target):
	A,B=pos;C,D=target
	if A!=C:return[_o if A<C else _p]
	if B!=D:return[_q if B<D else _r]
class InputHand:
	def __init__(A,base,plan_at,days=range(12,29),hour=3,hours=_B,max_workers=2,min_tiles=3,margin=1.5,reserve=3000,skip_days=(),wheat_reserve=60,beam=_E):B=hours;A.base=base;A.plan_at=plan_at;A.days=set(days);A.hour=hour;A.hours=set(B)if B else{hour};A.max_workers=max_workers;A.beam=beam;A.min_tiles=min_tiles;A.margin=margin;A.reserve=reserve;A.skip_days=set(skip_days);A.wheat_reserve=wheat_reserve;A.days_min=min(days);A.st={_K:-1};A.report=dict(hires=0,tiles=0,units=0,fert_bought=0,applied=0,errors=0)
	def forecast(R,obs,expected):
		G=obs;M=int(G[_K]);H=M//24;I=G[_O][G[_Q]];A=[list(I[_H])]+[list(A)for A in I[_C][:expected]];J={}
		for(S,T)in enumerate(I[_M]):
			for(U,B)in enumerate(T):
				if not isinstance(B,dict)or B.get(_U)not in CROPS:continue
				N=B[_U];V,O,W=CROPS[N]
				if 1<=H-B[_A3]<O:J[U,S]=dict(crop=N,birth=B[_A3],yld=B.get(_j,0),until=B.get(_AC,-1),watered=B.get(_AJ,_E),water=[],harvest=_B,first=V,last=O,cap=W)
		P=set()
		for C in range(M,min(712,(H+4)*24)):
			K=R.plan_at(C)or{};X=[K.get(_H)or[_J]]+list(K.get(_C)or[])
			for(F,E)in enumerate(X[:len(A)]):
				if not E:continue
				L=tuple(A[F]);D=J.get(L)
				if D is not _B and D[_AD]is _B:
					if E[0]==_A5 and(C//24,L)not in P:
						P.add((C//24,L))
						if not(C//24==H and D['watered'])and D[_AE]<=C//24-D[_AT]<=D['last']:D[_AU].append(C)
					if E[0]==_l:D[_AD]=C
				if E[0]in MOVES:Y,Z=MOVES[E[0]];A[F]=[max(0,min(9,A[F][0]+Y)),max(0,min(9,A[F][1]+Z))]
			for Q in K.get(_A)or[]:
				if Q and Q[0]==_W:a={B:sum(tuple(A)==B for A in A)for B in ACCESS};A.append(list(min(ACCESS,key=lambda p:(a[p],ACCESS.index(p)))))
			if(C+1)%24==0:A=[[4,4]]
		return J
	@staticmethod
	def gain(target,arrival,day):
		D='until';C=arrival;A=target
		if A[_AD]is _B or A[_AD]<=C:return 0
		B=sum(C<B<=A[_AD]and day<=B//24<=day+2 and B//24>A[D]for B in A[_AU]);E=A['yld']+sum(2 if B//24<=A[D]else 1 for B in A[_AU]);return max(0,min(B,A['cap']-E))
	def start(K,obs,action,index):
		C=action;B=obs;G=B[_O][B[_Q]];A=[list(G[_H])]+[list(A)for A in G[_C]]
		for(D,E)in enumerate(([C.get(_H)or[_J]]+list(C.get(_C)or[]))[:len(A)]):
			if E and E[0]in MOVES:H,I=MOVES[E[0]];A[D]=[max(0,min(9,A[D][0]+H)),max(0,min(9,A[D][1]+I))]
		J=sum(bool(A)and A[0]==_W for A in C.get(_A)or[]);F=ACCESS[0]
		for L in range(J+index+1):F=min(ACCESS,key=lambda p:(sum(tuple(A)==p for A in A),ACCESS.index(p)));A.append(list(F))
		return int(B[_K])+2,F
	def path_beam(K,obs,targets,action,index,width=8):
		D=obs;Q=int(D[_K]);L=Q//24;R,S=K.start(D,action,index);T={A:max(1,int(D[_A][_V][A])-2)for A in(_D,_P)};U=max(1,market_price(_I,D[_A][_m][_I]-16)+2);H=[(0,0,R,S,(),frozenset(),0,0)];A=_B
		for V in range(8):
			E=[]
			for(b,W,X,M,Y,N,Z,a)in H:
				for(B,I)in targets.items():
					if B in N:continue
					J=X+abs(M[0]-B[0])+abs(M[1]-B[1])
					if J>=L*24+23:continue
					F=K.gain(I,J,L)
					if not F:continue
					G=I[_U];O=W+F*T[G];P=Y+((B[0],B[1],G,I[_AT]),);E.append((O-1.5*U*len(P),O,J+1,B,P,N|{B},Z+(F if G==_D else 0),a+(F if G==_P else 0)))
			if not E:break
			E.sort(key=lambda s:(-s[0],-s[1],s[2],s[4]));H=E[:width]
			if V>=2:
				C=H[0]
				if A is _B or(-C[0],-C[1],C[2],C[4])<(-A[0],-A[1],A[2],A[4]):A=C
		if A is _B:return[],{_D:0,_P:0}
		return list(A[4]),{_D:A[6],_P:A[7]}
	def plans_joint(D,obs,action,targets,stock,purchases,topup):
		N=action;I=topup;H=obs;O=H[_O][H[_Q]];P=H[_A][_m];V=[A for A in N.get(_A)or[]if A];Q=[]
		for(W,R)in enumerate((_B,_D,_P)):
			J=dict(targets);E=[];B=0;A=0;K=0;F={_D:0,_P:0}
			for G in range(D.max_workers):
				X={B:A for(B,A)in J.items()if A[_U]==R}if G==0 and R else J;L,S=D.path_beam(H,X,N,G);C=len(L)
				if C<D.min_tiles or len(V)+2+G>10 or sum(stock.values())+purchases+B+C+I>95:break
				Y=market_price(_I,P[_I]-B-C-I);M=(C+(I if G==0 else 0))*(Y+2)+_fib(int(O[_AL])+G);T=sum(B*max(1,market_price(A,P[A]+F[A]+B)-2)for(A,B)in S.items())
				if T<D.margin*M+50 or O[_AA]<A+M+D.reserve:break
				E.append({_A1:L,_AV:C,_AM:_E});B+=C;A+=M;K+=T
				for(Z,a)in S.items():F[Z]+=a
				for(b,c,U,U)in L:J.pop((b,c),_B)
			Q.append(((K-A,K,-A,-len(E),-W),E,B,A,F))
		U,E,B,A,F=max(Q,key=lambda v:v[0]);return E,B,A,F
	def path(O,obs,targets):
		J=int(obs[_K]);K=J//24;E=J+4;F=4,4;G=dict(targets);H=[];L={_D:0,_P:0};P=obs[_A][_V]
		while G and len(H)<8:
			I=[]
			for(A,C)in G.items():
				B=E+abs(F[0]-A[0])+abs(F[1]-A[1]);D=O.gain(C,B,K);M=max(1,int(P[C[_U]])-2)
				if D and B<K*24+23:I.append((D*M/(B-E+1),D*M,-B,A,B,D))
			if not I:break
			N,N,N,A,B,D=max(I);C=G.pop(A);H.append((A[0],A[1],C[_U],C[_AT]));L[C[_U]]+=D;E=B+1;F=A
		return H,L
	def __call__(A,obs):
		C=obs;B=A.base(C)
		try:B=A.control(C,B);return A.surplus(C,B)
		except Exception:A.report['errors']+=1;return B
	def surplus(C,obs,action):
		Q='room';P='surplus';E=obs;D=action;K=int(E[_K]);R=K//24;S=K%24
		if K>=712 or R<C.days_min:return D
		B=[A for A in D.get(_A)or[]if A];N=E[_N][_Z];L=E[_A][_V];M=N.get(_D,0)
		if M>C.wheat_reserve and len(B)<10 and not any(A[0]in(_G,_S)and A[1]==_D for A in B):B=B+[[_G,_D,M-C.wheat_reserve]];C.report[P]=C.report.get(P,0)+M-C.wheat_reserve
		if S==23:
			F=projected_shed(E,D);T=sum(max(0,int(B))for A in E[_N][_R]for B in A.values());U=max(0,sum(F.values())-sum(N.values()));I={}
			for A in B:
				if A[0]==_G and len(A)>2:I[A[1]]=I.get(A[1],0)+int(A[2])
			V=sum(min(F.get(A,0),B)for(A,B)in I.items());J=sum(F.values())+(T-U)-V-99
			if J>0:
				W=[_D,_I,_P,_b]+sorted((A for A in F if A not in(_D,_I,_P,_b)and A in L),key=lambda p:L[p])
				for G in W:
					X=max(0,F.get(G,0)-I.get(G,0));H=min(J,X)
					if H<=0 or L.get(G,0)<1:continue
					O=_E
					for A in B:
						if A[0]==_G and len(A)>2 and A[1]==G:A[2]=int(A[2])+H;O=_F;break
					if not O:
						if len(B)>=10:break
						B.append([_G,G,H])
					J-=H;C.report[Q]=C.report.get(Q,0)+H
					if J<=0:break
		D=dict(D);D[_A]=B;return D
	def control(A,obs,action):
		k='day_requested';D=obs;C=action;N=int(D[_K]);E=N//24;S=N%24;l=D[_Q];F=D[_O][l];e=D[_N];B=A.st
		if N==0 or N<=B[_K]:B.clear();B.update(step=-1);A.report.update(hires=0,tiles=0,units=0,fert_bought=0,applied=0,errors=0)
		B[_K]=N
		if B.get(_A0)!=E:B.update(day=E,workers={},pending=_B)
		if B.get(_h):
			m=B.pop(_h)
			for(J,G)in m.items():
				if len(F[_C])>=J:B[_n][J]=G;A.report['hires']+=1
		if B[_n]:
			H=dict(C);H[_C]=list(C.get(_C)or[]);H[_C]=(H[_C]+[[_J]]*len(F[_C]))[:len(F[_C])]
			for(J,G)in B[_n].items():
				if J>len(F[_C]):continue
				n=e[_R][J]if J<len(e[_R])else{};f=tuple(F[_C][J-1]);T=[_J]
				if not G[_AM]:
					O=projected_shed(D,H);I=min(G[_AV],max(0,O.get(_I,0)))
					if I and f in ACCESS:T=[_a,_I,I];G[_AM]=_F
				elif n.get(_I,0):
					while G[_A1]:
						U,V,o,p=G[_A1][0];W=F[_M][V][U]
						if not isinstance(W,dict)or W.get(_U)!=o or W.get(_A3)!=p or W.get(_AC,-1)>=E+2:G[_A1].pop(0);continue
						T=_walk(f,(U,V))or[_AK]
						if T==[_AK]:G[_A1].pop(0);A.report['applied']+=1
						break
				H[_C][J-1]=T
			return H
		if S not in A.hours or E not in A.days or E in A.skip_days:return C
		P=[A for A in C.get(_A)or[]if A]
		if any(A[0]==_W for A in P):return C
		if B.get(k)==E:return C
		X=[A.plan_at(B)or{}for B in range(E*24,min((E+1)*24,719))];q=max(len(A.get(_C)or[])for A in X)
		if any(A and A[0]==_W for B in X[S:]for A in B.get(_A)or[]):return C
		Z=A.forecast(D,q);Q=[];L=0;a=0;R={_D:0,_P:0};O=projected_shed(D,C);g=sum(max(0,int(A[2]))for A in P if len(A)>2 and A[0]in(_S,_s));Y=max(0,O.get(_I,0))
		for K in P:
			if len(K)>=3 and K[0]==_G and K[1]==_I:Y=max(0,Y-max(0,int(K[2])))
			elif len(K)>=3 and K[0]==_S and K[1]==_I:Y+=max(0,int(K[2]))
		h=X[S+1]if S+1<len(X)else{};r=sum(max(0,int(A[2])if len(A)>2 else 1)for A in[h.get(_H)or[_J]]+list(h.get(_C)or[])if A and len(A)>1 and A[0]==_a and A[1]==_I);M=max(0,r-Y);i=D[_A][_m]
		if A.beam:Q,L,a,R=A.plans_joint(D,C,Z,O,g,M)
		else:
			for b in range(A.max_workers):
				c,j=A.path(D,Z);I=len(c)
				if I<A.min_tiles or len(P)+2+b>10 or sum(O.values())+g+L+I+M>95:break
				s=market_price(_I,i[_I]-L-I-M);d=(I+(M if b==0 else 0))*(s+2)+_fib(int(F[_AL])+b);t=sum(B*max(1,market_price(A,i[A]+R[A]+B)-2)for(A,B)in j.items())
				if t<A.margin*d+50 or F[_AA]<a+d+A.reserve:break
				Q.append({_A1:c,_AV:I,_AM:_E});L+=I;a+=d
				for(u,v)in j.items():R[u]+=v
				for(U,V,w,w)in c:Z.pop((U,V),_B)
		if not Q:return C
		B[_h]={len(F[_C])+1+A:B for(A,B)in enumerate(Q)};B[k]=E;A.report[_M]+=L;A.report['units']+=R[_D]+R[_P];A.report['fert_bought']+=L+M;H=dict(C);H[_A]=P+[[_S,_I,L+M]]+[[_W]for A in Q];return H
MOVES={_r:(0,-1),_q:(0,1),_o:(1,0),_p:(-1,0)}
PEN_TILES=[[(A,5)for A in range(5,8)],[(A,6)for A in range(5,8)]]
PEN_CYCLE={_c:(6,3),_f:(8,2),_i:(4,1)}
ANIMAL_COST={_c:500,_f:400,_i:300}
SEED_COST={_D:10,_P:20,_L:50,_e:100,_u:80}
def _fib(n):
	A,B=1,1
	for C in range(n):A,B=B,A+B
	return A
def _walk(pos,target):
	A,B=pos;C,D=target
	if A!=C:return[_o if A<C else _p]
	if B!=D:return[_q if B<D else _r]
class SheepPen:
	def __init__(A,base,plan_at,garden=_B,day0=12,min_yarn=2,min_wool=220,max_wheat=45,sheep=6,reserve=3000,daily_reserve=1000,animal=_c,gate=_B,lean=_E,endgame=_E):B=animal;A.endgame=endgame;A.lean=lean;A.animal=B;A.product={_c:_Y,_f:_X,_i:_b}[B];A.gate=gate;A.base=base;A.plan_at=plan_at;A.garden=garden;A.day0=day0;A.min_yarn=min_yarn;A.min_wool=min_wool;A.max_wheat=max_wheat;A.sheep=sheep;A.reserve=reserve;A.daily_reserve=daily_reserve;A.st={_AW:-1};A.report=dict(commits=0,hires=0,wool=0,fert=0,rescue=0,extra_wool=0,extra_fert=0,declines=0,errors=0)
	def eligible(A,obs):
		B=obs;C=B[_O][B[_Q]];E=B[_A][_V]
		if len(C[_M])!=10 or set(C.get(_z)or[])!={'NW','NE','SW'}:return _E
		F=(B.get(_w)or{}).get(_x)or[]
		if A.gate is not _B:
			if not A.gate(B):return _E
		elif F.count(_A7)<A.min_yarn or E[_Y]<A.min_wool or E[_D]>A.max_wheat:return _E
		if any(C[_M][A][B]!='LOCKED'for A in(5,6)for B in range(5,8)):return _E
		if B[_N][_Z].get(A.animal,0)or any(B.get(A.animal,0)for B in B[_N][_R]):return _E
		for G in range(A.day0*24,719):
			D=A.plan_at(G)or{}
			if any(B and(B[0]==_AB or B[0]==_s and B[1]==A.animal)for B in D.get(_A)or[]):return _E
			if any(B and B[0]in(_a,_d)and len(B)>1 and B[1]==A.animal for B in[D.get(_H)]+list(D.get(_C)or[])):return _E
		return _F
	def request(B,obs,action,st):
		N='declines';M='requested_day';E=obs;D=st;C=action;O=int(E[_K]);F=O//24;P=O%24
		if P>(2 if D.get(_AF)else 1)or D.get(M)==F:return C
		if not D.get(_AF)and(F!=B.day0 or not B.eligible(E)):return C
		Q=[B.plan_at(A)or{}for A in range(F*24,min((F+1)*24,719))]
		if any(A and A[0]==_W for B in Q[P+1:]for A in B.get(_A)or[]):return C
		I=E[_O][E[_Q]];J=[A for A in C.get(_A)or[]if A];R=sum(A[0]==_W for A in J);S=max(len(A.get(_C)or[])for A in Q)
		if len(I[_C])+R!=S:return C
		G=not D.get(_AF);T=E[_A][_V];K=B.hires_today(E,D,G)
		if K==0:D[M]=F;B.report[N]+=1;return C
		U=([[_AB],[_s,B.animal,B.sheep]]if G else[])+[[_S,_D,6]]+[[_W]]*K
		if len(J)+len(U)>10:return C
		W=projected_shed(E,C);L=6+B.sheep*G;H=(4000+ANIMAL_COST[B.animal]*B.sheep)*G+6*(int(T[_D])+10);H+=sum(_fib(A)for A in range(int(I[_AL]),int(I[_AL])+R+K))
		for A in J:
			if A[0]==_AB:return C
			if A[0]==_S and len(A)>2:L+=int(A[2]);H+=int(A[2])*(int(T[A[1]])+10)
			elif A[0]==_s and len(A)>2:L+=int(A[2]);H+=int(A[2])*ANIMAL_COST[A[1]]
			elif A[0]==_t and len(A)>2:H+=int(A[2])*SEED_COST[A[1]]
		if sum(W.values())+L>100:B.report[N]+=1;return C
		if I[_AA]<H+(B.reserve if G else B.daily_reserve):B.report[N]+=1;return C
		D[M]=F;D[_h]={_AE:S+1,_AX:G,'k':K};V=dict(C);V[_A]=J+U;return V
	def hires_today(B,obs,st,initial):
		H=initial;C=obs
		if B.endgame and not H:
			E=C[_O][C[_Q]];J=int(C[_K])//24;I,K=PEN_CYCLE[B.animal];D=_E
			for(F,G)in PEN_TILES[0]+PEN_TILES[1]:
				A=E[_M][G][F]
				if not(isinstance(A,dict)and A.get(_T)==B.animal):D=_F;break
				if A.get(_j,0)>=1:D=_F;break
				L=[B for B in range(J,29)if B+1-A.get(_AY,0)-I>=0 and(B+1-A.get(_AY,0)-I)%K==0]
				if L:D=_F;break
			if not D:return 0
		if not B.lean or H or int(C[_K])//24<=B.day0+1:return 2
		E=C[_O][C[_Q]]
		for(F,G)in PEN_TILES[0]+PEN_TILES[1]:
			A=E[_M][G][F]
			if not(isinstance(A,dict)and A.get(_T)==B.animal):return 2
			if A.get(_j,0)>=1:return 2
		return 1
	def worker(D,obs,actor,targets):
		T='cared_today';O=actor;K=obs;I=targets;P=K[_O][K[_Q]];J=K[_N];Q=int(K[_K]);B=tuple(P[_C][O-1]);F=J[_R][O];G=min(ACCESS,key=lambda p:(abs(B[0]-p[0])+abs(B[1]-p[1]),p));U=abs(B[0]-G[0])+abs(B[1]-G[1]);H=[A for A in(D.product,_I)if F.get(A,0)]
		if H and Q%24>=(22 if Q//24==29 else 23)-U:return _walk(B,G)or[_d,H[0],F[H[0]]]
		E=lambda x,y:P[_M][y][x];R=sum(not(isinstance(E(A,B),dict)and E(A,B).get(_T)==D.animal)for(A,B)in I)
		if R and not F.get(D.animal,0)and J[_Z].get(D.animal,0):return _walk(B,G)or[_a,D.animal,min(R,J[_Z][D.animal])]
		S=sum(not(isinstance(E(A,B),dict)and E(A,B).get(_AG))for(A,B)in I)
		if S and not F.get(_D,0)and J[_Z].get(_D,0):return _walk(B,G)or[_a,_D,min(S,J[_Z][_D])]
		L=[];V=len(I)>3 and any(isinstance(E(A,B),dict)and E(A,B).get(_T)==D.animal and not(E(A,B).get(_AG)and E(A,B).get(T))for(A,B)in I)
		for(W,(M,N))in enumerate(I):
			A=E(M,N);C=_B
			if A is _B:C=[_AZ]
			elif isinstance(A,dict)and A.get(_k)=='WEED':C=['DIG']
			elif isinstance(A,dict)and A.get(_k)=='PASTURE'and not A.get(_T):
				if F.get(D.animal,0):C=[_d,D.animal]
			elif isinstance(A,dict)and A.get(_T)==D.animal:
				if not A.get(_AG)and F.get(_D,0):C=[_AN]
				elif not A.get(T):C=['CARE']
				elif A.get(_j):C=[_l]
				elif A.get('fertilizer_available')and not V:C=[_Ab]
			if C:L.append((abs(B[0]-M)+abs(B[1]-N),W,(M,N),C))
		if L:X,X,Y,C=min(L);return _walk(B,Y)or C
		if H:return _walk(B,G)or[_d,H[0],F[H[0]]]
		return[_J]
	def rescue(I,obs,action,st):
		H='rescue_today';D=st;C=obs;A=action
		if not D[_n]or int(C[_K])%24>14:return A
		G=[A for A in A.get(_A)or[]if A]
		if len(G)>=10:return A
		if any(A[0]in(_W,_AB,_s,_S,_t)or len(A)>1 and A[1]==_D for A in G):return A
		E=C[_O][C[_Q]];J=C[_N];K=L=0;M=[A.get(_H)or[_J]]+list(A.get(_C)or[])
		for(F,R)in D[_n].items():
			N=M[F]if F<len(M)else[_J]
			if N==[_AN]or N[:2]==[_a,_D]:return A
			L+=J[_R][F].get(_D,0)if F<len(J[_R])else 0;K+=sum(isinstance(E[_M][B][A],dict)and E[_M][B][A].get(_T)==I.animal and not E[_M][B][A].get(_AG)for(A,B)in R)
		O=projected_shed(C,A);B=K-L-O.get(_D,0)
		if not 0<B<=6 or D.get(H,0)+B>6:return A
		P=int(C[_A][_V][_D])
		if P<1 or E[_AA]<1000+B*(P+10)or sum(O.values())+B>100:return A
		Q=dict(A);Q[_A]=G+[[_S,_D,B]];D[H]=D.get(H,0)+B;I.report['rescue']+=B;return Q
	def __call__(A,obs):
		B=A.base(obs)
		try:return A.control(obs,B)
		except Exception:A.report['errors']+=1;return B
	def control(B,obs,action):
		V='command';R='credit';Q='work';I=action;G=obs;H=int(G[_K]);O=H//24;A=B.st
		if H==0 or H<=A[_AW]:A.clear();A.update(last_step=-1,day=-1,workers={},work={},credit={B.product:0,_I:0});B.report.update(commits=0,hires=0,wool=0,fert=0,rescue=0,extra_wool=0,extra_fert=0,declines=0,errors=0)
		A[_AW]=H
		if O<B.day0:return I
		L=G[_O][G[_Q]];J=G[_N]
		if A.get(_A0)!=O:A.update(day=O,workers={},work={},rescue_today=0)
		for(E,P)in A.get(Q,{}).items():
			if P[_K]!=H-1 or E>=len(J[_R]):continue
			C={_l:B.product,_Ab:_I}.get(P[V][0])
			if C:S=max(0,J[_R][E].get(C,0)-P[_m].get(C,0));A[R][C]+=S;B.report['wool'if C==B.product else'fert']+=S
		F=A.pop(_h,_B)
		if F:
			W='SE'in(L.get(_z)or[])and(not F[_AX]or J[_Z].get(B.animal,0)>=B.sheep)
			if W and len(L[_C])>=F[_AE]+F.get('k',2)-1:
				if F.get('k',2)==1:A[_n][F[_AE]]=list(PEN_TILES[0])+list(PEN_TILES[1])
				else:
					for T in range(2):A[_n][F[_AE]+T]=list(PEN_TILES[T])
				B.report['hires']+=F.get('k',2)
				if F[_AX]:
					A[_AF]=_F;B.report['commits']+=1
					if B.garden is not _B:B.garden.blocked=_F
		I=B.request(G,I,A)
		if not A.get(_AF):return I
		D=dict(I);K=[D.get(_H)or[_J]]+list(D.get(_C)or[]);K+=[[_J]for A in range(len(L[_C])+1-len(K))];A[Q]={}
		for(E,X)in A[_n].items():
			if E>len(L[_C]):continue
			U=B.worker(G,E,X);K[E]=U;A[Q][E]={_K:H,V:U,_m:dict(J[_R][E])if E<len(J[_R])else{}}
		D[_H],D[_C]=K[0],K[1:];D=B.rescue(G,D,A);Y=projected_shed(G,D);M=[A for A in D.get(_A)or[]if A]
		for C in(B.product,_I):
			Z=sum(int(A[2])for A in M if A[0]==_G and len(A)>2 and A[1]==C);N=min(A[R][C],max(0,Y.get(C,0)-Z))
			if N and len(M)<10:M.append([_G,C,N]);A[R][C]-=N;B.report['extra_wool'if C==B.product else'extra_fert']+=N
		D[_A]=M;return D
MIN_DEFICIT=300
COW_MILK_SHOPS=3
def _plan_at(t):return plan(_CUR['obs'],t,flags_of=_CUR[_K])
def _cow_gate(obs):B=((obs.get(_w)or{}).get(_x)or[])[:4];A=obs[_A][_V];return sum(A in MILK_SHOPS for A in B)>=COW_MILK_SHOPS and A[_X]>=150 and A[_D]<=45
def _make():A=SETomato7(lambda o:_base_agent(o,_B),min_deficit=MIN_DEFICIT,big=400,big_opp=400,lean_offsets=(8,));_GARDEN[0]=A;B=InputHand(A,_plan_at,beam=_F,hours=(1,2,3));B=SheepPen(B,_plan_at,garden=A,lean=_F,endgame=_F);return B
_AGENT=_make()
ROW_HYGIENE=_F
LEAD_FERT=_F
FINAL_RERANK=_F
FEED_ECON=_F
GRAIN_OUTLET=_F
BUY_TRIM=_E
_F_ANIMAL_DAYS={_i:(4,1),_f:(8,2),_c:(6,3)}
_F_PRODUCT={_i:_b,_f:_X,_c:_Y}
_F_ACCESS=(4,4),(5,4),(4,5),(5,5)
_FST={_AO:0,_h:0,_A0:0,'skips':0,'sold':0,'trimmed':0}
_F_FEEDS={}
def _f_bonus_cost(tile,day):
	D=tile;A,E=_F_ANIMAL_DAYS[D[_T]];A+=int(D[_AY]);B=day+1;F=B>=A and(B-A)%E==0;G=max(0,int(D.get('pending_care_bonus',0)))if F else 0;C=A
	if C<=B:C+=((B-C)//E+1)*E
	H=0 if C>29 else 1;return G+H
def _f_plan_feeds(day):
	G=TAPE.route,day
	if G not in _F_FEEDS:
		E=[(4,4)];C=[0];I=set()
		for J in range(24):
			K=day*24+J
			if K>=len(TAPE):break
			H=TAPE[K]or{};M=[H.get(_H)or[_J]]+list(H.get(_C)or[])
			for(A,B)in enumerate(M[:len(E)]):
				if not B:continue
				D=E[A];F=B[0]
				if F in MOVES:N,O=MOVES[F];E[A]=max(0,min(9,D[0]+N)),max(0,min(9,D[1]+O))
				elif B[:2]==[_a,_D]and D in _F_ACCESS:C[A]+=max(0,int(B[2])if len(B)>2 else 1)
				elif F==_AN and C[A]>0:
					C[A]-=1
					if J<=21:I.add(D)
				elif F==_A4 and D in _F_ACCESS:C[A]=0
				elif B[:2]==[_d,_D]and D in _F_ACCESS:C[A]=max(0,C[A]-max(0,int(B[2])if len(B)>2 else 1))
			for L in H.get(_A)or[]:
				if L and L[0]==_W:P=min(_F_ACCESS,key=lambda p:(E.count(p),_F_ACCESS.index(p)));E.append(P);C.append(0)
		_F_FEEDS[G]=frozenset(I)
	return _F_FEEDS[G]
def _f_feed(obs,out):
	E=obs;A=out;I=int(E[_K]);B=I//24
	if not 10<=B<=28 or I%24>21:return A
	O=[TAPE[A]or{}for A in range(B*24,min(len(TAPE),B*24+24))];P=max(len(A.get(_C)or[])for A in O);G=E[_O][E[_Q]];H=[G[_H]]+list(G[_C]);F=[A.get(_H)or[_J]]+list(A.get(_C)or[]);J=E[_A][_V];K=E[_N][_R];L=_E
	for(C,Q)in enumerate(F[:P+1]):
		if Q!=[_AN]or C>=len(H)or C>=len(K):continue
		M,N=int(H[C][0]),int(H[C][1]);D=G[_M][N][M]
		if not isinstance(D,dict)or D.get(_T)not in _F_ANIMAL_DAYS:continue
		if D.get(_AG)or int(D.get('consecutive_unfed',0))!=0:continue
		if int(K[C].get(_D,0))<=0:continue
		R=_f_bonus_cost(D,B)
		if R*(float(J[_F_PRODUCT[D[_T]]])+5)*1.25>=float(J[_D]):continue
		if B<28 and(M,N)not in _f_plan_feeds(B+1):continue
		F[C]=[_J];L=_F;_FST[_AO]+=1;_FST['skips']+=1
	if not L:return A
	A=dict(A);A[_H]=F[0];A[_C]=F[1:];return A
def _f_outlet(obs,out):
	A=out;E=int(obs[_K]);F=E//24;G=E%24
	if F!=_FST[_A0]:_FST[_h]+=_FST[_AO];_FST[_AO]=0;_FST[_A0]=F
	if _FST[_h]<=0 or not 1<=G<=20 or E>=712:return A
	B=[list(A)for A in A.get(_A)or[]if A]
	if any(A[0]==_S and len(A)>1 and A[1]==_D for A in B):return A
	H=int(projected_shed(obs,A).get(_D,0))-sum(int(A[2])for A in B if A[0]==_G and len(A)>2 and A[1]==_D);C=min(_FST[_h],max(0,H))
	if C<=0:return A
	for D in B:
		if D[0]==_G and len(D)>2 and D[1]==_D:D[2]=int(D[2])+C;break
	else:
		if len(B)>=10:return A
		B.append([_G,_D,C])
	_FST[_h]-=C;_FST['sold']+=C;A=dict(A);A[_A]=B;return A
def _f_reserve(obs):
	A=int(obs[_K]);B=6
	for F in range(A+1,min(719,A+49)):
		C=TAPE[F]or{}
		for D in[C.get(_H)or[_J]]+list(C.get(_C)or[]):
			if D[:2]==[_a,_D]:B+=max(0,int(D[2])if len(D)>2 else 1)
		for E in C.get(_A)or[]:
			if len(E)>2 and E[:2]==[_G,_D]:B+=max(0,int(E[2]))
	if((obs.get(_w)or{}).get(_x)or[]).count(_A7)>=2:B+=6*len({A//24 for A in range(A+1,A+49)if A//24>=12})
	return B
def _f_trim(obs,out):
	C=obs;A=out;I=int(C[_K])
	if not 10<=I//24<=11:return A
	D=A.get(_A)or[]
	if not any(A and len(A)>2 and A[:2]==[_S,_D]and int(A[2])>0 for A in D):return A
	if any(A and A[:2]==[_G,_D]for A in D):return A
	G=max(0,int(projected_shed(C,A).get(_D,0)));J=_f_reserve(C);E=[]
	for B in D:
		if B and len(B)>2 and B[:2]==[_S,_D]:H=max(0,int(B[2]));F=min(H,max(0,J-G));G+=F;_FST['trimmed']+=H-F;E.append([_S,_D,F])
		else:E.append(B)
	A=dict(A);A[_A]=E;return A
def _r43f(obs,out):
	B=obs;A=out
	if int(B[_K])==0:_FST.update(saved=0,pending=0,day=0,skips=0,sold=0,trimmed=0)
	if FEED_ECON:A=_f_feed(B,A)
	if BUY_TRIM:A=_f_trim(B,A)
	if GRAIN_OUTLET:A=_f_outlet(B,A)
	return A
def agent(obs,config):
	B=obs;global _AGENT
	if int(B[_K])==0:TAPE.reset();_AGENT=_make()
	TAPE.select(B)
	if NO_GARDEN_ROUTED and TAPE.route is not _B and _GARDEN[0]is not _B:_GARDEN[0].blocked=_F
	A=_AGENT(B)
	if A:A=_r43f(B,A)
	if FINAL_RERANK and A:A=order_rows(dict(A),B,sales_first=_F,quote=_AR,hygiene=ROW_HYGIENE)
	return A