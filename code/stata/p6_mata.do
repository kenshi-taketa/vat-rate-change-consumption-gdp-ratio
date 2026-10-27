* ====================================================================
* P6 stage 6: Mata library (loaded by every step).  Independent re-implementation of the Python routines in p6est.py / conf2.py.
*   scmfast  : simplex least squares (primal active set; FISTA fallback if the KKT system is singular)
*   ascm     : ridge-augmented SCM, lambda by leave-one-quarter-out CV (w re-fitted), 1-SE rule, 41-point log grid 1e-6..1e2
*   runep    : treated + placebo-in-space for one episode  -> Stata matrices R (summary) and WT (weights)
*   confrun  : conformal sets (Chernozhukov-Wuthrich-Zhu) on the grid -30..+20 pp
* The panel is held in Mata globals PAN (rows t = 0..254, columns = countries) and CN (country codes).
* ====================================================================
mata: mata clear
mata:

void p6load()
{
    external real matrix PAN
    external string rowvector CN
    string rowvector nm
    real scalar j
    nm = st_varname(1..st_nvar())
    PAN = st_data(., nm)
    CN = J(1, 0, "")
    for (j=1; j<=cols(nm); j++) CN = CN, nm[j]
}

// rebased outcome: y (treated) and X (donors) over rows w0..t2 (t index), each series minus its first value
void getyx(string scalar tr, string scalar donors, real scalar w0, real scalar t2, real colvector y, real matrix X)
{
    external real matrix PAN
    external string rowvector CN
    string rowvector dn
    real scalar d, j
    real colvector v
    j = selectindex(CN :== "c_" + tr)
    v = PAN[(w0+1)::(t2+1), j]
    y = v :- v[1]
    dn = tokens(donors)
    X = J(rows(y), cols(dn), .)
    for (d=1; d<=cols(dn); d++) {
        j = selectindex(CN :== "c_" + dn[d])
        v = PAN[(w0+1)::(t2+1), j]
        X[., d] = v :- v[1]
    }
}

real colvector scmenum(real colvector y, real matrix X)
{
    real scalar nd, s, i, k, best, sse
    real colvector idx, b, sol, w, wb, r
    real matrix Xs, A
    nd = cols(X)
    best = .
    wb = J(nd, 1, 0)
    for (s=1; s<2^nd; s++) {
        idx = J(0, 1, .)
        for (i=1; i<=nd; i++) {
            if (mod(floor(s/2^(i-1)), 2) == 1) idx = idx \ i
        }
        k = rows(idx)
        Xs = X[., idx]
        A = (2*cross(Xs, Xs), J(k,1,1) \ J(1,k,1), 0)
        b = (2*cross(Xs, y) \ 1)
        sol = lusolve(A, b)
        if (missing(sol) > 0) continue
        w = sol[1::k]
        if (min(w) < -1e-10) continue
        r = y - Xs*w
        sse = cross(r, r)
        if (best >= . | sse < best - 1e-15) {
            best = sse
            wb = J(nd, 1, 0)
            wb[idx] = w
        }
    }
    wb = wb :* (wb :> 0)
    return(wb / sum(wb))
}

// projected-gradient (FISTA) fallback on the simplex
real colvector scmfista(real colvector y, real matrix X)
{
    real scalar n, L, it, tk, tn, i, rho, lam
    real matrix XtX
    real colvector Xty, w, z, wn, g, u, cs
    real colvector idx
    n = cols(X)
    XtX = cross(X, X)
    Xty = cross(X, y)
    L = 2*max(symeigenvalues(XtX))
    w = J(n, 1, 1/n)
    z = w
    tk = 1
    for (it=1; it<=200000; it++) {
        g = 2*(XtX*z - Xty)
        u = z - g/L
        // Euclidean projection onto the simplex
        cs = sort(u, -1)
        rho = 0
        lam = 0
        for (i=1; i<=n; i++) {
            if (cs[i] - (sum(cs[1::i]) - 1)/i > 0) {
                rho = i
                lam = (sum(cs[1::i]) - 1)/i
            }
        }
        wn = u :- lam
        wn = wn :* (wn :> 0)
        tn = (1 + sqrt(1 + 4*tk^2))/2
        z = wn + ((tk - 1)/tn)*(wn - w)
        if (max(abs(wn - w)) < 1e-14) {
            w = wn
            break
        }
        w = wn
        tk = tn
    }
    return(w / sum(w))
}

// exact simplex least squares: primal active-set method
real colvector scmfast(real colvector y, real matrix X)
{
    real scalar n, k, it, i, j0, al, a, m, vm, sc, nu
    real matrix XtX, A
    real colvector Xty, w, b, sol, v, ws, wn, g, act, S
    n = cols(X)
    if (n == 1) return(1)
    XtX = cross(X, X)
    Xty = cross(X, y)
    vm = .
    j0 = 1
    for (i=1; i<=n; i++) {
        if (vm >= . | XtX[i,i] - 2*Xty[i] < vm) {
            vm = XtX[i,i] - 2*Xty[i]
            j0 = i
        }
    }
    act = J(n, 1, 0)
    act[j0] = 1
    w = J(n, 1, 0)
    w[j0] = 1
    for (it=1; it<=60*n; it++) {
        S = selectindex(act)
        k = rows(S)
        A = (XtX[S, S], J(k,1,1) \ J(1,k,1), 0)
        b = (Xty[S] \ 1)
        sol = lusolve(A, b)
        if (missing(sol) > 0) return(scmfista(y, X))
        v = sol[1::k]
        if (min(v) < -1e-12) {
            ws = w[S]
            al = 1
            for (i=1; i<=k; i++) {
                if (v[i] < 0) {
                    a = ws[i]/(ws[i] - v[i])
                    if (a < al) al = a
                }
            }
            wn = ws + al*(v - ws)
            w = J(n, 1, 0)
            w[S] = wn
            for (i=1; i<=n; i++) {
                if (w[i] <= 1e-13) {
                    w[i] = 0
                    act[i] = 0
                }
            }
            if (sum(act) == 0) return(scmfista(y, X))
            continue
        }
        w = J(n, 1, 0)
        w[S] = v :* (v :> 0)
        g = XtX*w - Xty
        nu = mean(g[S])
        sc = 1 + max(abs(g))
        m = 0
        vm = 0
        for (i=1; i<=n; i++) {
            if (act[i] == 0) {
                if (g[i] - nu < vm) {
                    vm = g[i] - nu
                    m = i
                }
            }
        }
        if (m > 0) {
            if (vm < -1e-10*sc) {
                act[m] = 1
                continue
            }
        }
        return(w / sum(w))
    }
    return(scmfista(y, X))
}

// one-standard-error rule: largest lambda whose CV error is within one SE of the minimum
void picklam(real matrix sq, real rowvector grid, real scalar lam, real scalar lmin)
{
    real colvector m, se
    real scalar im, i, thr, n
    n = cols(sq)
    m = rowsum(sq)/n
    se = sqrt(rowsum((sq :- m):^2)/(n-1))/sqrt(n)
    im = 1
    for (i=2; i<=rows(m); i++) {
        if (m[i] < m[im]) im = i
    }
    thr = m[im] + se[im]
    lam = 0
    for (i=1; i<=rows(m); i++) {
        if (m[i] <= thr & grid[i] > lam) lam = grid[i]
    }
    lmin = grid[im]
}

// leave-one-quarter-out CV: both w and the ridge correction are re-estimated without quarter t
real matrix cvsq(real colvector y, real matrix X, real rowvector grid)
{
    real scalar T0, nd, t, i
    real matrix Xc, sq, A, Xk, Xck, V, ee
    real rowvector s
    real colvector keep, yk, wt, r, b, Vb, d
    T0 = rows(y)
    nd = cols(X)
    Xc = X :- rowsum(X)/nd
    sq = J(cols(grid), T0, .)
    for (t=1; t<=T0; t++) {
        keep = selectindex((1::T0) :!= t)
        yk = y[keep]
        Xk = X[keep, .]
        Xck = Xc[keep, .]
        wt = scmfast(yk, Xk)
        r = yk - Xk*wt
        A = cross(Xck, Xck)
        b = cross(Xck, r)
        symeigensystem(A, V, s)
        Vb = cross(V, b)
        for (i=1; i<=cols(grid); i++) {
            d = V*(Vb :/ (s' :+ grid[i]))
            ee = y[t] - X[t, .]*(wt + d)
            sq[i, t] = ee[1,1]^2
        }
    }
    return(sq)
}

// SCM or ridge-ASCM weights on the rows of (y, X); also returns lambda
real colvector ascmw(real colvector y, real matrix X, real scalar est, real scalar lam, real scalar lmin)
{
    real colvector w, delta
    real matrix Xc
    real rowvector grid
    w = scmfast(y, X)
    lam = .
    lmin = .
    if (est == 1) return(w)
    grid = 10:^(-6 :+ 0.2:*(0..40))
    picklam(cvsq(y, X, grid), grid, lam, lmin)
    Xc = X :- rowsum(X)/cols(X)
    delta = lusolve(cross(Xc, Xc) + lam*I(cols(X)), cross(Xc, y - X*w))
    return(w + delta)
}

real scalar olsslope(real colvector g)
{
    real scalar n
    real colvector h
    n = rows(g)
    h = (0::(n-1))
    return(cross(h :- mean(h), g :- mean(g)) / cross(h :- mean(h), h :- mean(h)))
}

// fit on rows 1..T0 of (y,X); returns (pre_rmspe_pp, post_rmspe_pp, ratio, mean_gap_pp, slope_pp_per_yr, lam, lmin); weights in wout
real rowvector fitep(real colvector y, real matrix X, real scalar T0, real scalar est, real colvector wout)
{
    real colvector w, g
    real scalar lam, lmin, pre, post, T
    real colvector gp
    T = rows(y)
    w = ascmw(y[1::T0], X[1::T0, .], est, lam, lmin)
    g = y - X*w
    pre = sqrt(mean(g[1::T0]:^2))
    gp = g[(T0+1)::T]
    post = sqrt(mean(gp:^2))
    wout = w
    return((100*pre, 100*post, post/pre, 100*mean(gp), 400*olsslope(gp), lam, lmin))
}

// episode: treated + placebos.  est: 1 = SCM, 2 = ASCM.  Results -> Stata matrices R (1 x 9) and WT (J x 1)
void runep(string scalar tr, string scalar donors, real scalar w0, real scalar t2, real scalar T0, real scalar est)
{
    real colvector y, wout, wd, yd
    real matrix X, Xd
    real rowvector r, rd
    real scalar nJ, j, nge, ratio, cnt
    string rowvector dn
    getyx(tr, donors, w0, t2, y, X)
    nJ = cols(X)
    r = fitep(y, X, T0, est, wout)
    ratio = r[3]
    nge = 0
    cnt = 0
    for (j=1; j<=nJ; j++) {
        yd = X[., j]
        Xd = X[., selectindex((1..nJ) :!= j)]
        rd = fitep(yd, Xd, T0, est, wd)
        if (rd[3] >= ratio - 1e-9) nge++
        if (rd[3] > ratio) cnt++
    }
    st_matrix("R", (r, (nge+1)/(nJ+1), 1+cnt, nJ))
    st_matrix("WT", wout)
}

// ---- conformal ----
real colvector scmu(real colvector y, real matrix X)
{
    return(y - X*scmfast(y, X))
}

real colvector augu(real colvector y, real matrix X)
{
    real scalar lam, lmin
    real colvector w
    w = ascmw(y, X, 2, lam, lmin)
    return(y - X*w)
}

real colvector pcurve(real matrix us, real scalar T0, real scalar T1, real scalar q)
{
    real scalar T, c, j
    real colvector u, s, p, blk
    T = rows(us)
    p = J(cols(us), 1, .)
    for (c=1; c<=cols(us); c++) {
        u = us[., c]
        s = J(T, 1, .)
        for (j=0; j<T; j++) {
            blk = u[mod((T0 + j) :+ (0::(T1-1)), T) :+ 1]
            if (q == 2) s[j+1] = sqrt(mean(blk :^ 2))
            else        s[j+1] = mean(abs(blk))
        }
        p[c] = mean(s :>= s[1] - 1e-15)
    }
    return(p)
}

real rowvector ciext(real colvector p, real colvector grid, real scalar alpha)
{
    real colvector acc
    acc = selectindex(p :> alpha)
    if (rows(acc) == 0) return((., ., 0))
    return((grid[min(acc)]*100, grid[max(acc)]*100, (min(acc) == 1 | max(acc) == rows(grid))))
}

// summary: p(0), pmax, theta_pmax (pp), ci90 lo hi edge, ci95 lo hi edge
real rowvector summ(real colvector p, real colvector grid)
{
    real scalar i, im, iz
    im = 1
    iz = 1
    for (i=2; i<=rows(p); i++) {
        if (p[i] > p[im]) im = i
        if (abs(grid[i]) < abs(grid[iz])) iz = i
    }
    return((p[iz], p[im], grid[im]*100, ciext(p, grid, 0.10), ciext(p, grid, 0.05)))
}

// spec: 1 SCM, 2 ASCM; step = grid step in pp (0.1 = as in the paper).  Rows of c_res: q=1, q=2.
void confrun(string scalar tr, string scalar donors, real scalar w0, real scalar t2, real scalar T0, real scalar spec, real scalar step)
{
    real colvector y0, y, grid
    real matrix X, us
    real scalar T, T1, c, n
    getyx(tr, donors, w0, t2, y0, X)
    T = rows(y0)
    T1 = T - T0
    n = round(50/step) + 1
    grid = (-30 :+ step:*(0::(n-1))) :/ 100
    us = J(T, n, .)
    for (c=1; c<=n; c++) {
        y = y0
        y[(T0+1)::T] = y[(T0+1)::T] :- grid[c]
        if (spec == 1) us[., c] = scmu(y, X)
        else           us[., c] = augu(y, X)
    }
    st_matrix("c_res", (summ(pcurve(us, T0, T1, 1), grid) \ summ(pcurve(us, T0, T1, 2), grid)))
}
end
