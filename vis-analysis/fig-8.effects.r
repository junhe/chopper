library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)


opening.comparison.versions.accumulated <- function()
{
    plot_percentiles_lines_allinone <- function(d)
    {
        dd_quantile <- function(d)
        {
            picks = c(0.8, 0.85, 0.9, 0.95, 0.99)
            #picks = seq(0.9, 1, 0.02)
            value = quantile(d$dspan, picks)
            percentilenames = paste(picks*100,"th%", sep="")
            ret = data.frame(percentile=picks,
                             percentilelabel=percentilenames,
                             bytes = value)
            ret$percentilelabel = factor(
                            ret$percentilelabel,
                            levels=percentilenames)
            return(ret)
        }

        breaks = seq(10, 36, 2)
        labs   = format_si(2^breaks, appendix="B")
        
        dd <- ddply(d, .(jobtag), dd_quantile)
        dd$percentile = factor(dd$percentile)

        ddg <<- dd
        dd$bytes = log2(dd$bytes)
        dd = rename_jobtag(dd)
        print(dd)
        p <- ggplot(dd, aes(x=jobtag,
                           y=bytes,
                           group=percentilelabel,
                           color=percentilelabel,
                           fill =percentilelabel)) +
             geom_line() +
             geom_point(size=3) +
             scale_color_grey(start=0) +       
             scale_y_continuous(breaks=breaks,
                                 labels=labs) +
             coord_cartesian(ylim=c(log2(1*2^20), log2(64*2^30)))+
             theme_paper() +
             theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
             theme(legend.position='none') +
             ylab("d-span (log scale)") +
             xlab("")

        return(p)
    }

    e2 <- arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity", #same as optspace, but setaffinity is removed, set number of CPU in sys
                "./data/agga.fixedimg-3.12.5.txt-inomodulo",    #LG prealloc=ino/10%2
                "./data/agga.fixedimg-3.12.5.txt-xSDxSE",
                "./data/agga.fixedimg-3.12.5.txt-xSDxSExSG",   #paper defined SD SE SG
                "./data/agga.fixedimg-3.12.5.txt-inomodNLBGNRT" # all problem fixed. inomodulo+nolastbig+goodnorm+rmtail, without setaffinity
                ))
                        
    d.long = e2$d.long   
    p = plot_percentiles_lines_allinone(d.long)
    return (p)
}

opening.comparison.versions.maineffect <- function()
{
    plot_percentiles_lines_allinone <- function(d)
    {
        dd_quantile <- function(d)
        {
            picks = c(0.8, 0.85, 0.9, 0.95, 0.99)
            value = quantile(d$dspan, picks)
            value = log2(value)
            print(value)
            stackvalues = c(value[1], value[-1]-value[-length(value)])
            print(stackvalues)
            percentilenames = paste(picks*100,"th%", sep="")
            ret = data.frame(percentile=picks,
                             percentilelabel=percentilenames,
                             bytes = value,
                             bytesstack = stackvalues)
            ret$percentilelabel = factor(
                            ret$percentilelabel,
                            levels=percentilenames)
            return(ret)
        }

        breaks = seq(10, 36, 2)
        labs   = format_si(2^breaks, appendix="B")
        
        dd <- ddply(d, .(jobtag), dd_quantile)
        dd$percentile = factor(dd$percentile)
        l = rev(levels(dd$percentile))
        dd$percentile = factor(dd$percentile, levels=l)
        print(levels(dd$percentile))

        dd = rename_jobtag(dd)

        p <- ggplot(dd, aes(x=jobtag,
                           y=bytes,
                           #y=bytesstack,
                           group=percentilelabel,
                           color=percentilelabel
                           #fill=percentilelabel
                           )) +
             geom_line() +
             geom_point(size=3) +
             #geom_bar(position='stack', stat='identity')+
             scale_color_grey(start=0) +       
             scale_y_continuous(breaks=breaks,
                                 labels=labs) +
             #geom_bar(stat='identity') +
             theme_paper() +
             theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
             theme(
                   legend.justification=c(0.1,0.1),
                   legend.position=c(0,0), 
                   legend.margin = unit(0, 'cm'),
                   legend.key.height = unit(0.5, 'strheight', '99th%'),
                   legend.key.width = unit(0.5, 'inches')
                   ) +
             theme(legend.background = element_blank()) +
             coord_cartesian(ylim=c(log2(1*2^20), log2(64*2^30)))+
             ylab("d-span (log scale)") +
             xlab("") +
             guides(color = guide_legend(reverse=TRUE), linetype = guide_legend(reverse=TRUE))

        return(p)
    }

    e1 <<- arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity", #same as optspace, but setaffinity is removed, set number of CPU in sys
                "./data/agga.fixedimg-3.12.5.txt-inomodulo",    #LG prealloc=ino/10%2
                "./data/agga.fixedimg-3.12.5.txt-optspaceRmtail",   #removed check for file tail extent
                "./data/agga.fixedimg-3.12.5.txt-nolastbig",        #do not reset goal group to last big file 
                "./data/agga.fixedimg-3.12.5.txt-optspacegoodnorm" #fixed bug in normalization
                ))
                        
    d.long = e1$d.long   
    p = plot_percentiles_lines_allinone(d.long)
    return (p)
}

main <- function()
{
    p1 = opening.comparison.versions.maineffect()
    p2 = opening.comparison.versions.accumulated()
    grid.arrange(p1, p2)

}

main()

