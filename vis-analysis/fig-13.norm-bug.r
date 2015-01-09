library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)


normalization.bug.effects <- function()
{
    goodnorm_all_effect_heatmap_forpaper <- function(dw)
    {
        make_sa_formula <- function(f)
        {
            factors = paste(f, collapse="+")
            fmstr = paste('behaviour~', factors, sep="")
            print(fmstr)
            fm = as.formula(fmstr)
            return(fm)
        }

        d = dw
        d$diff = d$xNB1cpu - d$nosetaffinity1cpu
        d$behaviour = abs(d$diff) > 1
        d$behaviour = factor(d$behaviour)
        
        d$file.size = format_si_factor(d$file.size, appendix="B")

        nams = list(c('file.size', 'fullness'))
        plot_list = list()
        for (factors in nams) {
            dd = as.data.frame(table(d[,c(factors, 'behaviour')]))

            factors = rename_factors(factors)
            names(dd) = rename_factors(names(dd))

            dd[,factors[1]] = factor(dd[,factors[1]])
            dd[,factors[2]] = factor(dd[,factors[2]])

            dd = subset(dd, behaviour == TRUE)

            p <- ggplot(dd, aes_string(x=factors[1], y=factors[2],
                              color='Freq')) +
                geom_point(size=4.5) +
                #facet_grid(.~behaviour) +
                scale_color_gradient("Count", low='white',
                                     high='black') +
                theme_paper()+
                theme(legend.title = element_blank()) +
                theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5))  +
                theme(legend.position='right')

            print(p)
        }
    }

    eppp <- arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity1cpu", # same as nosetaffinity, but always use 1 cpu
                "./data/agga.fixedimg-3.12.5.txt-xNB1cpu" #fixed norm bug, run with 1 cpu, no setaffinity
                ))
    goodnorm_all_effect_heatmap_forpaper(eppp$d.wide)
}


main <- function()
{
    normalization.bug.effects()
}

main()

