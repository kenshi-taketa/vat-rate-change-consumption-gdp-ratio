# ==========================================================================================
# P6 re-run B (R): (1) permutation test for the average gap of the 11 core increases,
#                  (2) motive comparison (type a vs type b) with the exact 50-arrangement test.
# Input : data/ascm_placebo_gaps_core11.csv  (written by the Python code: for each episode, the ridge-ASCM
#         mean gap (pp) of the treated country (unit = TREATED) and of every placebo country).
# What is independent: the aggregation, the random draws, the p-values, the enumeration of the 50 arrangements.
# What is NOT independent: the placebo gaps themselves (they come from Python).
# Run   : setwd("<folder that contains data/>"); source("B_permutation_and_motive.R")
# Output: B_results.csv ; compare with the Python values printed at the end (tolerances below).
# ==========================================================================================
d <- read.csv("data/ascm_placebo_gaps_core11.csv", stringsAsFactors = FALSE)
eps <- sort(unique(d$ep))
stopifnot(length(eps) == 11)
treated <- sapply(eps, function(e) d$mean_gap_pp[d$ep == e & d$unit == "TREATED"])
names(treated) <- eps
obs <- mean(treated)

## (1) permutation test: reference set of each episode = treated gap + placebo gaps (as in the paper)
set.seed(20261015); B <- 100000
draw <- sapply(eps, function(e) {
  ref <- d$mean_gap_pp[d$ep == e]                     # treated + placebos
  ref[sample.int(length(ref), B, replace = TRUE)]
})
perm <- rowMeans(draw)
p_one <- (sum(perm <= obs) + 1) / (B + 1)
p_two <- (sum(abs(perm) >= abs(obs)) + 1) / (B + 1)
q <- quantile(perm, c(0.025, 0.975))
cat(sprintf("\n(1) Core increases: mean gap = %.4f pp\n    one-sided p (<=) = %.4f, two-sided p = %.4f, middle 95%% of random averages = [%.3f, %.3f]\n",
            obs, p_one, p_two, q[1], q[2]))

## (2) motive comparison: type a vs type b, two period groups, exact enumeration
a_eps <- c("GB1979Q2", "GB1991Q2", "NZ2010Q4")
b_eps <- c("DE2007Q1", "GB2011Q1", "HU2012Q1", "JP1997Q2", "JP2014Q2", "NL2012Q4", "SI2013Q3")
grp1 <- c("NZ2010Q4", "GB2011Q1", "HU2012Q1", "NL2012Q4", "SI2013Q3")   # 2010-13
grp2 <- c("GB1979Q2", "GB1991Q2", "DE2007Q1", "JP1997Q2", "JP2014Q2")   # other years
stat_for <- function(bset) {
  tot <- 0; wsum <- 0
  for (g in list(grp1, grp2)) {
    isb <- g %in% bset; nb <- sum(isb); na <- sum(!isb); w <- na * nb / (na + nb)
    tot <- tot + w * (mean(treated[g][isb]) - mean(treated[g][!isb])); wsum <- wsum + w
  }
  tot / wsum
}
real <- stat_for(b_eps)
c1 <- combn(grp1, 4, simplify = FALSE)   # which 4 of the 5 episodes in 2010-13 get label b
c2 <- combn(grp2, 3, simplify = FALSE)   # which 3 of the 5 other episodes get label b
all_stats <- c()
for (x in c1) for (y in c2) all_stats <- c(all_stats, stat_for(c(x, y)))
stopifnot(length(all_stats) == 50)
n_ge <- sum(abs(all_stats) >= abs(real) - 1e-9)
cat(sprintf("\n(2) Motive comparison: weighted difference (b minus a) = %.3f pp\n    arrangements with |difference| >= |real|: %d of 50 -> p = %d/50 = %.2f\n",
            real, n_ge, n_ge, n_ge / 50))
cat(sprintf("    mean gap, type a = %.3f, type b = %.3f\n", mean(treated[a_eps]), mean(treated[b_eps])))
srt <- sort(abs(all_stats), decreasing = TRUE); cat("    four largest |difference| among the 50:", round(srt[1:4], 3), "\n")

res <- data.frame(item = c("core_mean_gap", "perm_p_one", "perm_p_two", "perm_q025", "perm_q975",
                           "motive_diff_b_minus_a", "motive_n_ge", "motive_p"),
                  R_value = c(obs, p_one, p_two, q[1], q[2], real, n_ge, n_ge / 50),
                  Python_value = c(-0.1215, 0.4869, 0.9054, NA, NA, -5.252, 2, 0.04))
write.csv(res, "B_results.csv", row.names = FALSE); print(res)
cat("\nTolerances: mean gap and motive numbers must match to 3 decimals; permutation p within 0.005 (random draws differ).\n")
