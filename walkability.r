#Normalized dataset on dropbox https://www.dropbox.com/s/yv707v7uhjyj9ni/Normalized_Dataframe.csv?dl=1
#Normal dataset https://www.dropbox.com/s/8imxwa4l9p44d46/Normal_Dataframe.csv?dl=1
require(foreign)
require(ggplot2)
require(MASS)
require(Hmisc)
require(reshape)
library(GGally)
#Tables
library(gt)
library(gtExtras)
library(tidyverse)
library(glue)

library(rmarkdown)

#Normalized dataframe
df = read.csv("https://www.dropbox.com/s/yv707v7uhjyj9ni/Normalized_Dataframe.csv?dl=1")
df <- head(df, -1)
attach(df)

tab1 = lapply(df[, c("Tot_Walk", "data.QC1", "data.QC2", "data.QC3", "data.QC4", "data.QC5", "data.QC6",
              "data.QC7", "data.QC8",  "data.QC9", "data.QC10" ,  "data.QC11", "data.QC12", "data.QC13",
              "data.QC14", "data.QC15", "data.QC16", "data.QC17", "data.QC18", "data.QC19", "data.QC20",
              "data.QC21",   "data.QC22",  "data.QC23", "data.QC24",  "data.QC25",  "data.QC26", "data.QC27",
              "data.QC28", "data.QC29", "data.QC30")], table)

print("Table of descriptive statistics Tot_Walk vs data.QC1 - data.QC30:")
print(tab1)

var = "Tot_Walk"

print("Summary Tot_Walk:")
print(summary(Tot_Walk))

#Ordered logistic regression: Fitting the ordinal logistic regression model
#Fit ordered logit model and store results 'olm'
method = c("logistic")

olm <- polr(formula = as.factor(Tot_Walk) ~ data.QC1 + data.QC2 + data.QC3 + data.QC4 + data.QC5 + data.QC6 + data.QC7 +
             data.QC8 + data.QC9 + data.QC10 + data.QC11 + data.QC12 + data.QC13 + data.QC14 + data.QC15 +
             data.QC16 + data.QC17 + data.QC18 + data.QC19 + data.QC20 + data.QC21 + data.QC22 + data.QC23 +
             data.QC24 + data.QC25 + data.QC26 + data.QC27 + data.QC28 + data.QC29 + data.QC30, data = df, Hess=TRUE)

print("A summary of the fitted model, Tot_Walk vs data.QC1 - data.QC30:")
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

print("Modeling with Second approach -- RMS")
library(rms)
Y <- cbind(Tot_Walk)
#print(summary(Y))

X <- cbind(data.QC1, data.QC2, data.QC3, data.QC4, data.QC5, data.QC6,
              data.QC7, data.QC8,  data.QC9, data.QC10 , data.QC11, data.QC12, data.QC13,
              data.QC14, data.QC15, data.QC16, data.QC17, data.QC18, data.QC19, data.QC20,
              data.QC21, data.QC22, data.QC23, data.QC24, data.QC25, data.QC26, data.QC27,
              data.QC28, data.QC29, data.QC30)
Xvar <- c("data.QC1", "data.QC2", "data.QC3", "data.QC4", "data.QC5", "data.QC6",
              "data.QC7", "data.QC8",  "data.QC9", "data.QC10" ,  "data.QC11", "data.QC12", "data.QC13",
              "data.QC14", "data.QC15", "data.QC16", "data.QC17", "data.QC18", "data.QC19", "data.QC20",
              "data.QC21",   "data.QC22",  "data.QC23", "data.QC24",  "data.QC25",  "data.QC26", "data.QC27",
              "data.QC28", "data.QC29", "data.QC30")

#Descriptive Statistics
print("Summary Y:")
print(summary(Y))

print("Summary X:")
#print(summary(X))

print("Table Y:")
print(table(Y))

print("Ordered logit model coefficients:")
ddist <- datadist(Xvar)
options <- (datadist='ddist')

ologit <- lrm(Y~X, data=df)
print(ologit)

#Ordered logit model odds ratio
#summary(ologit) #Complains of error

print("Ordered logit model predicted probabilities:")
xmeans <- colMeans(X)
new_data = data.frame(t(xmeans))
print(new_data)

print("Model fitting:")
fitted <- predict(ologit, newdata = df, type = "fitted.ind")
colMeans(fitted)
