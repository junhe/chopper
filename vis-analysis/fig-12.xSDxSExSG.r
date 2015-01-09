library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)


xSDxSExSG.interaction_heatmap.highlight <- function()
{
    interaction_heatmap_tail <- function(d)
    {
        make_sa_formula <- function(f)
        {
            factors = paste(f, collapse="+")
            fmstr = paste('dspan~', factors, sep="")
            print(fmstr)
            fm = as.formula(fmstr)
            return(fm)
        }

        threshold = as.numeric(quantile(d$dspan, 0.9))*0.9
        d$file.size = format_si_factor(d$file.size, appendix="B")

        nams = list(
                    c('chunk.order','fullness'))
        plot_list = list()
        for (factors in nams) {
            fm = make_sa_formula(factors)
            dd = aggregate(fm, data=d, max)
            dd$cut = dd$dspan >= threshold
            dd$cut = factor(dd$cut)
            dd$cut = factor(dd$cut, levels=rev(levels(dd$cut)))
            levels(dd$cut) = revalue(levels(dd$cut), 
                                     c("TRUE"="With tail",
                                       "FALSE"="Without tail"))

            dd[,factors[1]] = factor(dd[,factors[1]])
            dd[,factors[2]] = factor(dd[,factors[2]])
            names(dd) = rename_factors(names(dd))
            factors = rename_factors(factors)
        
            p <- ggplot(dd, aes_string(x=factors[1], y=factors[2], color="cut")) +
                 geom_point(size=4) +
                 scale_color_grey(start=0) +
                 theme_paper() +
                 theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
                 theme(legend.key = element_blank()) +
                 theme(legend.direction = 'horizontal')


            fname = 'ChunkOrderFullnessxSDxSExSGInter'
            if (all(factors == 
                    rename_factors(c('chunk.order','fullness')))) {
                ww = 5
                hh = 2.5
            }
            print(p)
        }
    }

    ettx <- arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-xSDxSExSG"
                ))
    d = ettx$d.long
    interaction_heatmap_tail(d)
}

main <- function()
{
    xSDxSExSG.interaction_heatmap.highlight() 
}

main()


