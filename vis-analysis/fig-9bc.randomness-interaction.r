library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)

randomness.interaction.heatmap.highlight <- function()
{
    schedulerdependency.all_effect_heatmap_forpaper <- function(dw)
    {
        make_sa_formula <- function(f)
        {
            factors = paste(f, collapse="+")
            fmstr = paste('behaviour~', factors, sep="")
            print(fmstr)
            fm = as.formula(fmstr)
            return(fm)
        }

        # it returns a list containing vectors,
        # each item is one that we want to know the level mean
        get_set <- function(nways) 
        {
            #nams = c("sync","chunk.order","file.size","dir.span",
                     #"fsync")

            #nams = c("disk.size", "sync","chunk.order", "file.size", "fullness",
                     #"num.cores", "fsync", "num.files", "layoutnumber",
                     #"disk.used", "dir.span")
            #nams = c('num.cores', 'num.files')
            nams = c('file.size', 'num.cores', 'chunk.order')
            
            a = combn(nams, nways)
            #print(a)
            a = alply(a, 2)
            #print(a)
            return(a)
        }
        d = dw
        #d$diff = d$optspacegoodnorm - d$optspace
        d$diff = d$nosetaffinity02 - d$nosetaffinity
        d$behaviour = abs(d$diff) > 1
        d$behaviour = factor(d$behaviour)
        
        d$file.size = format_si_factor(d$file.size, appendix="B")

        #nams=get_set(2)
        #nams = list(c('num.cores','file.size'),
                    #c('chunk.order','file.size'))

        nams = list(c('file.size','num.cores'),
                    c('file.size','chunk.order'))
        plot_list = list()
        for (factors in nams) {
            #factors = rev(factors)
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
                theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) 

            #print(p)
            plot_list = append(plot_list, list(p))
        }
        do.call("grid.arrange", c(plot_list))
    }

    e <- arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity", #same as optspace, but setaffinity is removed, set number of CPU in sys
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity02"
                ))
    d.wide = e$d.wide
    
    schedulerdependency.all_effect_heatmap_forpaper(d.wide)
}


main <- function (){
    randomness.interaction.heatmap.highlight()
}

main()

