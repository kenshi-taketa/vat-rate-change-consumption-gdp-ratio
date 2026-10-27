# ==========================================================================================
# P6 final re-run, step R2 (R): (a) compare the Stata fits with the Python fits unit by unit (treated country and every placebo country),
# (b) rebuild every row of Table F1 (Appendix F) from the fits, with the permutation test of Section 5.4, and compare with the table.
# Input : output/stata_long.csv (Stata, ASCM), output/ife_long_r.csv (R3), data/python_long.csv, data/gsynth_all_p6_results.csv (gsynth run, R)
# Output: output/R2_unit_comparison.csv, output/R2_tableF1_check.csv
# Run   : setwd("<folder rerun_final_20261025>"); source("R/R2_compare_and_aggregate.R")
# ==========================================================================================
S <- read.csv("output/stata_long.csv", stringsAsFactors = FALSE)
P <- read.csv("data/python_long.csv", stringsAsFactors = FALSE)

## ---- (a) unit-level comparison, Stata vs Python ------------------------------------------------
Pa <- P[P$tag != "ife", ]
m <- merge(S, Pa, by = c("ep", "tag", "unit"), all = TRUE, suffixes = c("_S", "_py"))
m$missing <- is.na(m$m_all_S) | is.na(m$m_all_py)
cmp <- do.call(rbind, lapply(split(m, m$tag), function(d) { k <- !d$missing
  data.frame(tag = d$tag[1], runs = length(unique(d$ep)), units_compared = sum(k), units_only_in_one = sum(d$missing),
             max_diff_m_all = max(abs(d$m_all_S - d$m_all_py)[k]), max_diff_m_skipL = max(abs(d$m_skipL_S - d$m_skipL_py)[k]),
             max_diff_m_skip2 = max(abs(d$m_skip2_S - d$m_skip2_py)[k]), max_diff_pre_rmspe = max(abs(d$pre_rmspe_S - d$pre_rmspe_py)[k]),
             max_rel_diff_ratio = max((abs(d$ratio_S - d$ratio_py) / d$ratio_py)[k])) }))
write.csv(cmp, "output/R2_unit_comparison.csv", row.names = FALSE); cat("\n(a) Stata vs Python, all units:\n"); print(cmp, digits = 3)
cat("Expected: units_only_in_one = 0; differences in gaps below 0.01 pp; relative difference of the ratio below 0.005.\n")

## ---- (b) Table F1 --------------------------------------------------------------------------------
inc <- c("DE2007Q1", "GB1979Q2", "GB1991Q2", "GB2011Q1", "HU2012Q1", "JP1997Q2", "JP2014Q2", "LU2015Q1", "NL2012Q4", "NZ2010Q4", "SI2013Q3")
sets <- list(all11 = inc, exJP2014 = setdiff(inc, "JP2014Q2"), exEuro = setdiff(inc, c("HU2012Q1", "NL2012Q4", "SI2013Q3")))
B <- 100000; set.seed(20261015)
agg <- function(L, eps) {     # L: data frame with ep, unit, v (TREATED and placebos); equal weights; reference set = placebos + treated
  eps <- eps[eps %in% L$ep]; if (!length(eps)) return(c(n = 0, est = NA, p_two = NA, p_one = NA))
  obs <- sapply(eps, function(e) L$v[L$ep == e & L$unit == "TREATED"]); est <- mean(obs)
  draws <- sapply(eps, function(e) { ref <- L$v[L$ep == e]; ref[sample.int(length(ref), B, replace = TRUE)] }); perm <- rowMeans(draws)
  c(n = length(eps), est = est, p_two = (sum(abs(perm) >= abs(est)) + 1) / (B + 1), p_one = (sum(perm <= est) + 1) / (B + 1))
}
get <- function(df, tag, col) { d <- df[df$tag == tag, ]; data.frame(ep = d$ep, unit = d$unit, v = d[[col]]) }
G <- read.csv("data/gsynth_all_p6_results.csv", stringsAsFactors = FALSE); gs <- data.frame(ep = G$ep, unit = ifelse(G$is_treated == 1, "TREATED", G$unit), v = G$mean_gap_pp)
Ife <- read.csv("output/ife_long_r.csv", stringsAsFactors = FALSE)
rowsA <- list(
  list("Main estimate (ASCM)",                          get(S, "main", "m_all"),    c(-0.12,.91, .27,.81, .44,.75)),
  list("Drop the first two post-treatment quarters",    get(S, "main", "m_skip2"),  c(-0.07,.95, .35,.77, .54,.71)),
  list("Treatment date one quarter earlier",            get(S, "lead1", "m_skipL"), c(.26,.77, .68,.49, 1.11,.34)),
  list("Treatment date two quarters earlier",           get(S, "lead2", "m_skipL"), c(-0.28,.76, .06,.95, .46,.69)),
  list("Hong Kong and Taiwan added",                    get(S, "hktw", "m_all"),    c(-0.23,.83, .20,.86, .25,.85)),
  list("Factor model, our own code (R3)",               get(Ife, "ife", "m_all"),   c(-0.09,.93, .40,.70, .28,.82)),
  list("Factor model, gsynth",                          gs,                          c(.10,.94, .59,.68, 1.48,.38)),
  list("Eurostat series",                               get(S, "esvint", "m_all"),  c(-0.28,.81, .15,.91, .13,.93)))
out <- list()
for (r in rowsA) for (k in seq_along(sets)) { a <- agg(r[[2]], sets[[k]]); t <- r[[3]][(2 * k - 1):(2 * k)]
  out[[length(out) + 1]] <- data.frame(panel = "A", row = r[[1]], set = names(sets)[k], n = a["n"], est_R = a["est"], p_two_R = a["p_two"], est_table = t[1], p_two_table = t[2],
                                       est_ok = abs(a["est"] - t[1]) < 0.006, p_ok = abs(a["p_two"] - t[2]) < 0.012) }
rowsB <- list(list("Pre-treatment window of 60 quarters", "pre60", 0.21, 11), list("Pre-treatment window of 80 quarters (7 episodes)", "pre80", 0.06, 7),
              list("Full pre-treatment history", "prefull", 0.08, NA), list("No rate change in the pre-treatment window (10 episodes)", "restricted", 0.55, 10),
              list("No data-break rule", "nobreakrule", -0.29, 11))
p1 <- c()
for (r in rowsB) { a <- agg(get(S, r[[2]], "m_all"), inc); p1 <- c(p1, a["p_one"])
  out[[length(out) + 1]] <- data.frame(panel = "B", row = r[[1]], set = "all11", n = a["n"], est_R = a["est"], p_two_R = a["p_two"], est_table = r[[3]], p_two_table = NA,
                                       est_ok = abs(a["est"] - r[[3]]) < 0.006, p_ok = NA) }
T <- do.call(rbind, out); rownames(T) <- NULL; write.csv(T, "output/R2_tableF1_check.csv", row.names = FALSE)
cat("\n(b) Table F1 rebuilt from the fits:\n"); print(T, digits = 3)
cat("\nPanel B one-sided p-values (table note: range 0.42 to 0.79):", round(range(p1), 2), "\n")
cat("Expected: est_ok TRUE in every row (two decimals), p_ok TRUE (the random draws differ: tolerance 0.012).\n")
