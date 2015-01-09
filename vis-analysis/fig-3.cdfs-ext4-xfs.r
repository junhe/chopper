library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)
library(devtools)


xfs.ecdf.forpaper <- function()
{
    arrange.data.env <- function(files)
    {

        gd <- load_files_by_parameters(files)
        gd$all.dspan = gd$dspan
        gd$dspan = gd$max.dspan
        d.wide <- make_it_wide(gd)
        gd <- gd
        d.wide <- d.wide
        return (list(d.long=gd, d.wide=d.wide))
    }

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
        print(summary(dd))

        quanss <- ddply(d, .(jobtag), 
                     function(x) {quantile(x$dspan/2^30, c(.9,.95,1))})
        print(quanss)
        
        dd$jobtag = factor(dd$jobtag)
        l = levels(dd$jobtag)
        #dd$jobtag = factor(dd$jobtag, levels=rev(l))
        
        p <- ggplot(dd, aes(x=bytes,
                            y=percentile,
                            color=jobtag))+
              geom_line() +
              ylab("Cumulative Density") +
              xlab("d-span (GB)") +
              scale_color_grey(start=0.6, 
                               end=0
                               )+
              scale_x_continuous(breaks=breaks,
                                 labels=nms) +
              scale_y_continuous(breaks=seq(0,1,0.1))+
              coord_cartesian(xlim = c(-2*2^30, 68*2^30),
                              ylim = c(0, 1.1)) +
              theme_paper() +
              theme(legend.position=c(0.5,0.5))
        print(p)
        #save_plot(p, 'ext4vsxfs', w=5, h=2.5)

        return()
    }
    
    e = arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity", #same as optspace, but setaffinity is removed, set number of CPU in sys
                "./data/agga.fixedimg-3.12.5.txt-xfsNewNosetaffinity" # xfs with optspace. No setaffinity
                ))
    d.long = e$d.long 
    d.long$jobtag = factor(d.long$jobtag)
    lvs = c(
            "xfsNewNosetaffinity"="xfs-vanilla",
            "nosetaffinity"="ext4-vanilla")
    levels(d.long$jobtag) = revalue(levels(d.long$jobtag),
                                    c("nosetaffinity"="ext4-vanilla",
                                      "xfsNewNosetaffinity"="xfs-vanilla"))
    levels(d.long$jobtag) = revalue(levels(d.long$jobtag),lvs)
    d.long$jobtag = factor(d.long$jobtag, levels=lvs)
    print(levels(d.long$jobtag))

    plot_ecdf_only2(d.long)
}


main <- function()
{
    xfs.ecdf.forpaper()
}

main()

