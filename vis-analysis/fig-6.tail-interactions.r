library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)

evaluation.interaction_heatmap.highlight <- function()
{

    interaction_heatmap_tail <- function(d)
    {
        make_sa_formula <- function(f)
        {
            factors = paste(f, collapse="+")
            fmstr = paste('dspan~', factors, sep="")
            fm = as.formula(fmstr)
            return(fm)
        }

        # it returns a list containing vectors,
        # each item is one that we want to know the level mean
        get_set <- function(nways) 
        {
            nams = c("sync","chunk.order","file.size","dir.span",
                     "fsync")

            a = combn(nams, nways)
            a = alply(a, 2)
            return(a)
        }
        
        threshold = as.numeric(quantile(d$dspan, 0.9))*0.9
        #threshold = 1*2^30
        d$file.size = format_si_factor(d$file.size, appendix="B")

        #nams=get_set(2)
        nams = list(
                    c('file.size', 'fsync'),
                    c('chunk.order', 'fsync'))
        plot_list = list()
        for (factors in nams) {
            fm = make_sa_formula(factors)
            dd = aggregate(fm, data=d, max)
            dd$cut = dd$dspan >= threshold
            #dd$cut = cut(dd$dspan, 
                                #c(0,   2^c(10,20,30,40)),
                         #labels=c("Byte", "KB","MB","GB")
                         #)
            #mybreaks = c(0, 2^seq(10,40,1))
            #n = length(mybreaks)
            #dd$cut = cut(dd$dspan, 
                         #mybreaks,
                         #labels=format_si(mybreaks)[-n]
                         #)
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

            #print(p)
            plot_list = append(plot_list, list(p))
        }
        do.call("grid.arrange", c(plot_list, ncol=2))
    }

    e = arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity" #same as optspace, but setaffinity is removed, set number of CPU in sys
                ))
    d = e$d.long
    interaction_heatmap_tail(d)
}



main <- function()
{
    evaluation.interaction_heatmap.highlight()
}

main()

