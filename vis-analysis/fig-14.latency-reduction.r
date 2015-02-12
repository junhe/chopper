library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)
library(RCurl)

setwd('/Users/junhe/workdir/chopper/vis-analysis/')

analyze_randomized <- function()
{
    theme_paper <- function()
    {
        return (  theme_bw() +
                  theme(axis.line    =element_line(color='black')) +
                  theme(panel.border =element_rect(color='black')) +
                  theme(legend.position='top') +
                  theme(legend.direction = 'horizontal') +
                  theme(legend.key = element_blank()) +
                  #theme(legend.key.height = unit(0, 'cm')) +
                  #theme(legend.key.width = unit(0.5, 'cm')) +
                  theme(legend.margin = unit(0, 'cm')) +
                  theme(strip.background = element_rect(colour = "white", 
                                                        fill = "white",
                                                        size = 1))
                  )
    }

    file = './data/fixfilesize.random1.10.100'
    if (exists('USE.REMOTE.CHOPPER') && USE.REMOTE.CHOPPER == TRUE) {
        path = paste('https://raw.githubusercontent.com/junhe/chopper/master/vis-analysis/', 
                     file, sep="")
        print(path)
        datatext <- getURL(path)
        d = read.table(text=datatext, header=T)
    } else {
        path = file
        d = read.table(file=path, header=T)
    }


    d = subset(d, nfiles %in% c(1, 10))
    d = subset(d, ncpus < 64)

    d$version = ifelse(d$nextents != 1, 'SD', '!SD')

    d = aggregate(duration~ncpus+mode+version+nfiles, 
                  data = d, mean)

    d$duration = 1000*d$duration
    d$mode = factor(d$mode)
    levels(d$mode) = revalue(levels(d$mode), c('r'='Read',
                                             'w'='Write'))
    d$nfiles = factor(d$nfiles)
    d$ncpus = factor(d$ncpus)

    p = ggplot(d, aes(x=ncpus, y=duration, 
                      linetype=version, group=version))+
            geom_point() +
            geom_line() +
            facet_grid(mode~nfiles, scales='free_y', 
                       labeller=function(x1,x2) 
                        {
                            if (x1=='nfiles') {
                                suffixes = ifelse(as.numeric(levels(x2)) == 1, 'file', 'files')
                                mat = cbind(levels(x2), suffixes)
                                newlevels = apply(mat, 1, paste, collapse=' ')
                                levels(x2) = newlevels
                                return(newlevels)
                            } else {
                                return (as.character(x2))
                            }
                        }
                       ) +
            scale_color_grey(start=0, end=0.5) +
            expand_limits(y=0) +
            scale_linetype('Version:') +
            xlab('Number of Creating Threads') +
            ylab('Access Time (ms)') +
            theme_paper()

    print(p)
}

main <- function()
{
    analyze_randomized()
}

main()
