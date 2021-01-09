# Measuring inequalities in urban systems: An approach for evaluating the distribution of amenities and burdens
#### T.M.Logan, M.J.Anderson, T.G.Williams, L.Conrow
A public repository used in the creation of the recent publication, [Measuring inequalities in urban systems: An approach for evaluating the distribution of amenities and burdens](https://www.sciencedirect.com/science/article/pii/S0198971520303239)

**Please cite as:**
`Logan, T., Anderson, M., Williams, T., and Conrow, L. “Measuring Inequality in the built environment: an approach for evaluating the distribution of amenities and burdens”. Computers, Environment and Urban Systems. `

![](https://ars.els-cdn.com/content/image/1-s2.0-S0198971520303239-ga1_lrg.jpg)

## Overview
In this publication, we analysed the inequality of network-based accessibility to supermarkets in 10 major US cities. We did this by utilising open-source data for supermarket locations and census data at a census block level. Technically, we leveraged our previous work on [OSRM Network Query](https://github.com/urutau-nz/query_access_osrm) to calculate the nearest network distance and [Inequalipy: Measuring inequality among distributions](https://pypi.org/project/inequalipy/) to evaluate the inequality among the distance distribution. This repository is used as a demonstration of just one example where inequalipy can be used within the urban environment. Other examples include distributions of both "goods" (where a high value is typically favourable, e.g. income) and "bads" (where a low value is typically favourable, e.g. exposure to a natural hazard).

## Utilising Query Access OSRM
Using OSRM and Python we calculated the nearest distance from residents homes to their nearest supermarket. [This blog post](https://urutau.co.nz/how-to/osrm/) describes this process.

## Utilising Inequalipy
As part of this publication, we developed a Python and R package to quickly and efficiently calculate inequality among distributions. [This package](https://pypi.org/project/inequalipy/) provides functions for the following:

* Kolm-Pollak Equally-Distributed Equivalent (EDE) and Index
* Atkinson EDE and Index
* Gini Index
