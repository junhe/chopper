library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)

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
    nosharedgoal_factormapping.highlight() #fig 10 b,c
}

main()

