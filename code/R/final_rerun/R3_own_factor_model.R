# ==========================================================================================
# P6 final re-run, step R3 (R): our own factor model (stage 5, "IFE") re-implemented in R.
# Method (same as the paper's Appendix F1, written here from the description, not copied from the Python code):
#   window = 40 pre + 20 post quarters, series rebased to 0 at the first pre quarter; comparison countries as in the main analysis.
#   Fit on the comparison countries only: time effect b_t (row mean), country effect (column mean of the rest), factors = left singular vectors
#   of the remainder (scaled by sqrt(T)). The treated country is regressed on a constant and the first r factors over the pre-quarters;
#   r (0 to 5) is chosen by leaving out one pre-quarter at a time (first minimum).  Placebos: every comparison country in turn,
#   with the other comparison countries.
# Input : data_r/p6_wide_main_r.csv and data_r/variants_r.csv (from R1_build_inputs.R), data/python_long.csv (Python result, for comparison)
# Output: output/ife_long_r.csv (same layout as stata_long.csv, tag = ife) and output/R3_check_ife.csv
# Run   : setwd("<folder rerun_final_20261025>"); source("R/R3_own_factor_model.R")      (about a minute)
# ==========================================================================================
V <- read.csv("data_r/variants_r.csv", stringsAsFactors = FALSE); V <- V[V$tag == "main", ]
W <- read.csv("data_r/p6_wide_main_r.csv", check.names = FALSE); rownames(W) <- W$t; W$t <- NULL; names(W) <- sub("^c_", "", names(W))
ife_fit <- function(Y0m, y1, T0, rmax = 5) {
  T <- nrow(Y0m); J <- ncol(Y0m)
  b <- rowMeans(Y0m); Z <- Y0m - b; a <- colMeans(Z); Z <- sweep(Z, 2, a, "-")
  U <- svd(Z)$u; yt <- y1 - b[1:T0]; best_m <- Inf; best_r <- 0
  for (r in 0:min(rmax, J - 1, T0 - 4)) {
    F <- cbind(1, if (r > 0) U[, 1:r, drop = FALSE] * sqrt(T) else NULL)
    err <- sapply(1:T0, function(t) { k <- setdiff(1:T0, t); cf <- lm.fit(F[k, , drop = FALSE], yt[k])$coefficients; (yt[t] - sum(F[t, ] * cf))^2 })
    if (mean(err) < best_m) { best_m <- mean(err); best_r <- r }
  }
  r <- best_r; F <- cbind(1, if (r > 0) U[, 1:r, drop = FALSE] * sqrt(T) else NULL)
  cf <- lm.fit(F[1:T0, , drop = FALSE], yt)$coefficients
  list(fit = b + as.numeric(F %*% cf), r = r)
}
summ <- function(y, fit, T0) { g <- y - fit; gp <- g[1:T0]; gq <- g[(T0 + 1):length(g)]
  c(pre_rmspe = 100 * sqrt(mean(gp^2)), ratio = sqrt(mean(gq^2)) / sqrt(mean(gp^2)), m_all = 100 * mean(gq), m_skipL = 100 * mean(gq), m_skip2 = 100 * mean(gq[-(1:2)])) }
out <- list()
for (i in seq_len(nrow(V))) {
  ep <- V$ep[i]; tr <- V$cc[i]; don <- strsplit(V$donors[i], " ")[[1]]; T0 <- V$T0[i]
  rows <- as.character(V$w0[i]:V$t2[i]); D <- as.matrix(W[rows, c(tr, don)]); D <- sweep(D, 2, D[1, ], "-")
  one <- function(unit, pool) { f <- ife_fit(D[, pool, drop = FALSE], D[1:T0, unit], T0); c(summ(D[, unit], f$fit, T0), r = f$r) }
  res <- rbind(c(one(tr, don)), t(sapply(don, function(j) one(j, setdiff(don, j)))))
  out[[ep]] <- data.frame(ep = ep, tag = "ife", unit = c("TREATED", don), res, row.names = NULL)
  cat(ep, "J =", length(don), " r =", res[1, "r"], " mean gap =", round(res[1, "m_all"], 3), "\n")
}
L <- do.call(rbind, out); write.csv(L, "output/ife_long_r.csv", row.names = FALSE)
P <- read.csv("data/python_long.csv", stringsAsFactors = FALSE); P <- P[P$tag == "ife", ]
m <- merge(L, P, by = c("ep", "tag", "unit"), suffixes = c("_R", "_py"))
chk <- do.call(rbind, lapply(split(m, m$ep), function(d) data.frame(ep = d$ep[1], n_units = nrow(d), n_units_py = sum(P$ep == d$ep[1]),
  r_treated_R = d$r_R[d$unit == "TREATED"], r_treated_py = d$r_py[d$unit == "TREATED"], r_same_all_units = all(d$r_R == d$r_py),
  max_diff_m_all = max(abs(d$m_all_R - d$m_all_py)), max_diff_pre_rmspe = max(abs(d$pre_rmspe_R - d$pre_rmspe_py)), max_diff_ratio = max(abs(d$ratio_R - d$ratio_py)))))
write.csv(chk, "output/R3_check_ife.csv", row.names = FALSE); print(chk)
cat("\nExpected: same number of units, same factor numbers r, and differences below 0.01 (gap, pp) / 0.005 (ratio). Small differences can occur when two\nvalues of r have almost the same cross-validation error.\n")
