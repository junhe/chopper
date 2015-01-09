library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)


xSDxSE.interaction_heatmap.highlight <- function()
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
            #nams = c("sync","chunk.order","file.size","dir.span",
                     #"fsync")

            nams = c("disk.size", "sync","chunk.order", "file.size", "fullness",
                     "num.cores", "fsync", "num.files", "layoutnumber",
                     "disk.used", "dir.span")
            
            a = combn(nams, nways)
            a = alply(a, 2)
            return(a)
        }
        
        threshold = as.numeric(quantile(d$dspan, 0.9))*0.9
        print(sprintf("threshold:%f", threshold/2^30))
        d$file.size = format_si_factor(d$file.size, appendix="B")

        nams = list(
                    c('chunk.order','file.size'))
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
                 geom_point(size=5) +
                 scale_color_grey(start=0) +
                 theme_paper() +
                 theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
                 theme(legend.key = element_blank())

            breaknums = c(8,   64,   72,    128, 256)
            myvjust   = c(0.5, 1,    0.5,   0.5, 0.5)
            mybreaks = paste(breaknums, 'KB', sep="")

            fname = paste(factors, collapse="")
            fname = paste(fname, 'xSDxSEInter', sep="")
            ww = 5
            hh = 2.9

            print(p)
        }
    }

    exxddd <<- arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-xSDxSE"
                ))
    d = exxddd$d.long
    interaction_heatmap_tail(d)
}


main <- function()
{
    xSDxSE.interaction_heatmap.highlight()
}

main()

