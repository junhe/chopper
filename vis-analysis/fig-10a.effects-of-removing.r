library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)


specialend_factormapping <- function()
{
    do_factor_mapping_dspandiff_specialend.cut <- function(d)
    {
        behave_distr <- function(d, f)
        {
           #d$diff = d$optspacegoodnorm - d$optspace
           d$diff = d$myNospecialEnd1CPU - d$nosetaffinity1cpu
           d$behaviour = cut(d$diff, c(-Inf, -1, 1, Inf), labels=c('Reduced','Unchanged','Increased'))
           #d$behaviour = cut(d$diff, c(-Inf, -1, 1, Inf), labels=c('"-" ','"=" ','"+"  '))
           #print(table(d$diff))

           d = as.data.frame(table(d[,c(f, 'behaviour')]))

           f   = rename_factors(f)
           names(d) = rename_factors(names(d))

           d[,f] = factor(d[,f])
           #levels(d$behaviour) = revalue(levels(d$behaviour),
                                         #c('TRUE'='affected',
                                           #'FALSE'='not affected'))
           print(summary(d$behaviour))
                                        
           print (f)
           p <- ggplot(d, aes_string(x=f, y='Freq', fill='behaviour')) +
                geom_bar( aes(order=behaviour),
                         position='stack', 
                             stat='identity')+
                #geom_text(aes(label=Freq), 
                          #position=position_dodge(width=1), vjust=-0.1, size=4)+
                scale_fill_grey(start=0) +       
                #scale_x_discrete(breaks=seq(0,256*1024, 16*1024),
                                 #labels=format_2exp(appendix="B"))+
                #expand_limits( y=c(0, yupper)) +
                xlab(f) +
                ylab("Count") +
                theme_paper() +
                theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
                theme(legend.position='none') 
           return(p)
        }
        nams = names(d)
        print(nams)
        nams = c("sync")
        d$file.size = format_si_factor(d$file.size, appendix="B")

        plot.list = list()
        for (nm in nams) {
            p <- behave_distr(d, nm)
            plot.list = append(plot.list, list(p))
        }
        do.call("grid.arrange", c(plot.list))
    }


    e.xxff <<- arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity1cpu", #same as optspace, but setaffinity is removed, set number of CPU in sys
                "./data/agga.fixedimg-3.12.5.txt-myNospecialEnd1CPU"
                ))
    d.wide = e.xxff$d.wide

    do_factor_mapping_dspandiff_specialend.cut(d.wide)
}

nosharedgoal_factormapping.highlight <- function()
{
    nosharedgoal.do_factor_mapping_dspandiff_cut <- function(d)
    {
        behave_distr <- function(d, f)
        {
           d$diff = d$tagNolastbig1CPU - d$nosetaffinity1cpu
           d$behaviour = cut(d$diff, c(-Inf, -1, 1, Inf), labels=c('Reduced','Unchanged','Increased'))

           d = as.data.frame(table(d[,c(f, 'behaviour')]))

           f   = rename_factors(f)
           names(d) = rename_factors(names(d))

           d[,f] = factor(d[,f])
           print(summary(d$behaviour))
           
           p <- ggplot(d, aes_string(x=f, y='Freq', fill='behaviour')) +
                geom_bar( aes(order=behaviour),
                         position='stack', 
                             stat='identity')+
                scale_fill_grey(start=0) +       
                xlab(f) +
                ylab("Count") +
                theme_paper() +
                theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
                theme(legend.background = element_blank()) +
                theme(legend.margin = unit(0, 'cm'))

           return(p)
        }
        nams = names(d)
        nams = c("file.size", "fullness")
        d$file.size = format_si_factor(d$file.size, appendix="B")

        plot.list = list()
        for (nm in nams) {
            p <- behave_distr(d, nm)
            plot.list = append(plot.list, list(p))
        }
        do.call("grid.arrange", c(plot.list))
    }

    e.xjjfdnx <- arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity1cpu", #same as optspace, but setaffinity is removed, set number of CPU in sys
                "./data/agga.fixedimg-3.12.5.txt-tagNolastbig1CPU"
                ))
    d.wide = e.xjjfdnx$d.wide

    nosharedgoal.do_factor_mapping_dspandiff_cut(d.wide)
}


main <- function()
{
    specialend_factormapping()  #fig 10 a
}

main()

