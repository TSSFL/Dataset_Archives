#Normalized dataset on dropbox https://www.dropbox.com/s/yv707v7uhjyj9ni/Normalized_Dataframe.csv?dl=1
#Normal dataset https://www.dropbox.com/s/8imxwa4l9p44d46/Normal_Dataframe.csv?dl=1

# Only two packages are actually used by this script: MASS for polr() and rms
# for lrm(). foreign, ggplot2, Hmisc, reshape, GGally, gt, gtExtras, tidyverse,
# glue and rmarkdown were loaded here but never called - and one of them being
# absent (gtExtras) was enough to stop the whole script before it read any data.
if (!requireNamespace("MASS", quietly = TRUE)) {
  stop("R package 'MASS' is required but not available here.", call. = FALSE)
}
library(MASS)

# The caller sets ivar before sourcing, e.g.
#   assign("ivar", "Totbususage")
# Response variables in this dataset:
#   "PT.Buses..1strip."  "PT.Buses..Ltrip."  "TotWalk..1stTrp."
#   "Totbususage"        "Tot_Walk"
if (!exists("ivar")) {
  stop("Set 'ivar' before sourcing this script, e.g. ivar <- \"data.QC31\"", call. = FALSE)
}

#Normalized dataframe
df = read.csv("https://www.dropbox.com/s/yv707v7uhjyj9ni/Normalized_Dataframe.csv?dl=1")
df <- head(df, -1)

# Fail here with a readable message rather than inside lapply() further down.
if (!ivar %in% names(df)) {
  stop(sprintf("ivar '%s' is not a column of the dataset.\n  Response variables available: %s",
               ivar, paste(setdiff(names(df), grep("^data\\.QC", names(df), value = TRUE)),
                           collapse = ", ")), call. = FALSE)
}

attach(df)

tab1 = lapply(df[, c(ivar, "data.QC1", "data.QC2", "data.QC3", "data.QC4", "data.QC5", "data.QC6",
              "data.QC7", "data.QC8",  "data.QC9", "data.QC10" ,  "data.QC11", "data.QC12", "data.QC13",
              "data.QC14", "data.QC15", "data.QC16", "data.QC17", "data.QC18", "data.QC19", "data.QC20",
              "data.QC21",   "data.QC22",  "data.QC23", "data.QC24",  "data.QC25",  "data.QC26", "data.QC27",
              "data.QC28", "data.QC29", "data.QC30")], table)

print(sprintf("Table of descriptive statistics %s vs data.QC1 - data.QC30:", ivar))
print(tab1)

#https://stackoverflow.com/questions/5215481/remove-quotes-from-a-character-vector-in-r
print(sprintf("Summary of %s:", ivar))
print(summary(get(ivar)))

#Ordered logistic regression: Fitting the ordinal logistic regression model
#Fit ordered logit model and store results 'olm'
method = c("logistic")
 
olm <- polr(formula = as.factor(get(ivar)) ~ data.QC1 + data.QC2 + data.QC3 + data.QC4 + data.QC5 + data.QC6 + data.QC7 +
             data.QC8 + data.QC9 + data.QC10 + data.QC11 + data.QC12 + data.QC13 + data.QC14 + data.QC15 +
             data.QC16 + data.QC17 + data.QC18 + data.QC19 + data.QC20 + data.QC21 + data.QC22 + data.QC23 +
             data.QC24 + data.QC25 + data.QC26 + data.QC27 + data.QC28 + data.QC29 + data.QC30, data = df, Hess=TRUE)
 
print(sprintf("A summary of the fitted model, %s vs data.QC1 - data.QC30:", ivar))
print(summary(olm))

#Calculating p values
 
#First we store the coefficient table, then calculate the p-values and combine back with the table.
#Store table
(ctable <- coef(summary(olm)))
 
#Calculate and store p values
p <- pnorm(abs(ctable[, "t value"]), lower.tail = FALSE)*2
 
#Combined table
print("p values and the coefficient table:")
coeff_and_p_values = (ctable <- cbind(ctable, "p value" = p))
print(coeff_and_p_values)
 
print("Profiled CIs (95% CI) from the default method:")
cis = (ci <- confint(olm))
print(cis)
 
print("CIs assuming normality:")
cis_nor = confint.default(olm)
print(cis_nor)
 
print("Odds ratios:")
oddr1 = exp(coef(olm))
print(oddr1)
 
print("Odds ratios including CI:")
oddr2 = exp(cbind(OR = coef(olm), ci))
print(oddr2)
 
print("Modeling with Second approach")

Xvar <- c("data.QC1", "data.QC2", "data.QC3", "data.QC4", "data.QC5", "data.QC6",
          "data.QC7", "data.QC8", "data.QC9", "data.QC10", "data.QC11", "data.QC12",
          "data.QC13", "data.QC14", "data.QC15", "data.QC16", "data.QC17", "data.QC18",
          "data.QC19", "data.QC20", "data.QC21", "data.QC22", "data.QC23", "data.QC24",
          "data.QC25", "data.QC26", "data.QC27", "data.QC28", "data.QC29", "data.QC30")

Y <- get(ivar)
X <- df[, Xvar]

print("Summary Y:")
print(summary(Y))

print("Table Y:")
print(table(Y))

print("Summary X:")
print(summary(X))

if (requireNamespace("rms", quietly = TRUE)) {
  # Preferred route when rms is installed: lrm() gives the full model report.
  library(rms)
  ddist <- datadist(X)
  options(datadist = "ddist")
  ologit <- lrm(as.factor(Y) ~ ., data = cbind(Y = Y, X))
  print("Ordered logit model (rms::lrm):")
  print(ologit)
  fitted_probs <- predict(ologit, newdata = df, type = "fitted.ind")
} else {
  # rms is absent in this environment, so the same quantities are produced from
  # the MASS model already fitted above rather than abandoning the analysis.
  message("Package 'rms' not available - using the MASS model for the same quantities.")
  fitted_probs <- predict(olm, newdata = df, type = "probs")
}

print("Predicted probabilities at the predictor means:")
xmeans <- colMeans(X)
new_data <- as.data.frame(t(xmeans))
print(predict(olm, newdata = new_data, type = "probs"))

print("Mean predicted probability per response category across the sample:")
print(colMeans(fitted_probs))
