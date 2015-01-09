library(grid)
library(ggplot2)
library(combinat)
library(gridExtra)
library(plyr)
library(reshape2)
library(R.utils)


randomness.varitaion.cdf <- function()
{
    schedulerdependency.diff.hist <- function (d)
    {
        d$diff = d$nosetaffinity02 - d$nosetaffinity
        d$diff = abs(d$diff)
        d = subset(d, diff > 1)

        d$diff = d$diff/2^30
        maxdiff = max(d$diff)

        print(quantile(d$diff, seq(0,1,0.1)))

        func_ecdf = ecdf(d$diff)
        
        NBREAKS = 1024*2
        xbreaks = seq(0, maxdiff, length.out=NBREAKS)
        ys = func_ecdf(xbreaks)
        dd = data.frame(bytes=xbreaks,
                         percentile=ys)

        p <- ggplot(dd, aes(x=bytes,
                            y=percentile)) +
            geom_line() +
            scale_x_continuous(breaks=seq(0, 64, 4))+
            scale_y_continuous(breaks=seq(0,1,0.1))+
            coord_cartesian(xlim = c(-1, maxdiff+2),
                              ylim = c(0, 1.05)) +
            theme_paper() +
            ylab("Cumulative\nDensity") +
            xlab("d-span difference (GB)") 

        print(p)
    }
    e = arrange.data.env(files=c(
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity", #same as optspace, but setaffinity is removed, set number of CPU in sys
                "./data/agga.fixedimg-3.12.5.txt-nosetaffinity02"
                ))
    schedulerdependency.diff.hist(e$d.wide)
}

main <- function()
{
    randomness.varitaion.cdf()
}

main()

