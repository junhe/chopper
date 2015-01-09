library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)


opening.ecdf <- function()
{
    plot_ecdf_only2 <- function(d)
    {
        breaks = seq(0, 64*2^30, 8*2^30)
        nms = paste(breaks/2^30)

        ddply_ecdf <- function(d)
        {
            NBREAKS = 1024*2
            xbreaks = seq(0, 64*2^30, length.out=NBREAKS)
            func_ecdf = ecdf(d$dspan)
            ys = func_ecdf(xbreaks)
            ret = data.frame(bytes=xbreaks,
                             percentile=ys)
            return (ret)
        }

        d = rename_jobtag(d)

        dd = ddply(d, .(jobtag), ddply_ecdf)
        dd$jobtag = factor(dd$jobtag)
        l = levels(dd$jobtag)
        
        p <- ggplot(dd, aes(x=bytes,
                            y=percentile,
                            color=jobtag))+
              geom_line() +
              ylab("Cumulative Density") +
              xlab("d-span (GB)") +
              scale_color_grey(start=0.6, end=0,
                               breaks=c("!(SD | SE | SG | NB)",
                                        "Vanilla"),
                               labels=c("Final",
                                        "Vanilla")
                               )+
              scale_x_continuous(breaks=breaks,
                                 labels=nms) +
              scale_y_continuous(breaks=seq(0,1,0.1))+
              coord_cartesian(xlim = c(-2*2^30, 68*2^30),
                              ylim = c(0, 1.1)) +
              theme_paper() +
              #theme(legend.position='None')
              theme(legend.position=c(0.5,0.5))
        print(p)
    }
    
    e = arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity", #same as optspace, but setaffinity is removed, set number of CPU in sys
                "./data/agga.fixedimg-3.12.5.txt-inomodNLBGNRT" # all problem fixed. inomodulo+nolastbig+goodnorm+rmtail, without setaffinity
                ))
                        
    d.long = e$d.long
    plot_ecdf_only2(d.long)
}

main <- function()
{
    opening.ecdf()
}

main()

