library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)


evaluation.factor.mapping.percentage.highlight.align <- function()
{

    do_factor_mapping_oneplot <- function(d)
    {
        behave_distr <- function(d, f)
        {
           threshold = quantile(d$dspan, 0.9)
           print(paste('threshold:', threshold/2^30))
           d$behaviour = d$dspan < threshold

           d = as.data.frame(table(d[,c(f, 'behaviour')]))
           d$behaviour = mapvalues(d$behaviour, 
                              from = c(TRUE, FALSE),
                              to   = c("Non-Tail", "Tail"))
           if ( f == 'jobtag' ) {
                print(d)
           }
           d[,f] = factor(d[,f])
           flabel = rename_factors(f)
           
           print(d)
           
           # get total
           fmstr = paste('Freq','~', f, sep="")
           total.fm = as.formula(fmstr)
           d.total = aggregate(total.fm, data=d, sum)
           #print(d.total)

           d.tail = subset(d, behaviour=='Tail')
           #print(d.tail)
           d.merge = merge(d.tail, d.total, by=f, sort=F)
           d.merge$Percentage = with(d.merge, 100*Freq.x/Freq.y)
           print(d.merge)
          
           mybreaks = c(0, 10, 20, 30)
           mylabels = paste(mybreaks, '%', sep="") 

           p <- ggplot(d.merge, aes_string(x=f, y='Percentage')) +
                geom_bar(position='stack', stat='identity', fill='black') +
                #geom_text(aes(label=Freq), 
                          #position=position_dodge(width=1), vjust=-0.1, size=4)+
                #scale_fill_grey(start=0) +       
                #scale_x_discrete(breaks=seq(0,256*1024, 16*1024),
                                 #labels=format_2exp(appendix="B"))+
                #expand_limits( y=c(0, yupper)) +
                #xlab(flabel) +
                scale_y_continuous(breaks=mybreaks, labels=mylabels) +
                #xlab(NULL) +
                ylab(NULL) +
                theme_paper() +
                theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
                coord_cartesian(ylim = c(-0.5, 31)) 
          
           #if ( f == 'file.size' ) {
                #p <- p + 
                #theme(axis.text.x=element_text(size=7,
                                               #angle=90, 
                                               #hjust=1, 
                                               #vjust=0.5)) 
           #}
           #print(p)
           return(p)
        }
        nams = names(d)
        nams = c("file.size", "disk.size", "sync", "chunk.order", "fullness",
                 "num.cores", "fsync", "num.files", "layoutnumber",
                 "disk.used", "dir.span")

        plot.list = list()
        for (nm in nams) {
            #mcf_filter(d, nm)
            #behave_distr(d,nm)
            p <- behave_distr(d, nm)
            plot.list = append(plot.list, list(p))
            fname = paste(nm, 'distr', sep="")
        }
        do.call("grid.arrange", c(plot.list, ncol=4))
    }

    e = arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity" #same as optspace, but setaffinity is removed, set number of CPU in sys
                ))
    d.long = e$d.long
    d.long$disk.size = format_si_factor(d.long$disk.size, 
                                        appendix="B")
    d.long$file.size = format_si_factor(d.long$file.size,
                                        appendix="B")
    do_factor_mapping_oneplot(d.long)
    
}


main <- function()
{
    evaluation.factor.mapping.percentage.highlight.align()
}

main()

