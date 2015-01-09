library(ggplot2)
library(plyr)
library(grid)

theme_paper <- function()
{
    return (  theme_bw() +
              theme(axis.line    =element_line(color='black')) +
              theme(panel.grid   =element_blank()) +
              theme(panel.border =element_blank()) +
              theme(legend.key = element_blank())
              )
}

format_si <- function(x, show.number=T, show.unit=T, round.to=1, appendix="") {
   {
    exps <- seq(10, 70, by=10)
    limits <- c(0, 2^exps) # 0, 1024, 1024*1024, ...
    prefix <- c("", "K", "M", "G", "T", "P", "E", "Z")
  
    # Vector with array indices according to position in intervals
    indices <- findInterval(abs(x), limits)
    limits[1] = 1
    number = NULL
    if ( show.number ) {
        number = format(round(x/limits[indices], round.to),
                 trim=TRUE, scientific=FALSE)
    }
    unit = NULL
    if ( show.unit ) {
        unit = prefix[indices]
    }
    paste(number, unit, appendix, sep="")
  }
}

format_2exp <- function(round.to=1, appendix="", ...) {
   function (x) {
    exps <- seq(10, 70, by=10)
    limits <- c(0, 2^exps) # 0, 1024, 1024*1024, ...
    prefix <- c("", "K", "M", "G", "T", "P", "E", "Z")
  
    # Vector with array indices according to position in intervals
    i <- findInterval(abs(x), limits)
    limits[1] = 1
    print(length(x))
    ret = paste(format(round(x/limits[i], round.to),
                 trim=TRUE, scientific=FALSE, ...),
          prefix[i], appendix, sep="")
    return(ret)
  }
}

build_df <- function(meanlog, sdlog)
{
  x=seq(0,30,length=100)
  y=dlnorm(x, meanlog=meanlog, sdlog=sdlog)
  d=data.frame(x=x,y=y)
  d$meanlog = meanlog
  d$sdlog = sdlog
  return(d)
}

get_filepath <- function(f) {
    f = gsub(".", "-", f, fixed=T)
    filename = paste(f, '-auto.pdf', sep="")
    filepath = paste('./', filename, sep="")
    return(filepath)
}

save_plot <- function(p, f, w=4, h=4) {
    filepath = get_filepath(f)
    print(paste("about to save to", getwd(), filepath))
    print("enter -s- if you want to save to pdf")
    a = readline()
    if (a == 's') {
        ggsave(filepath, plot=p, width=w, height=h)
    }
}

plot_dists <- function(d)
{
    d = ddply(d, .(meanlog, sdlog), function(x){build_df(x$meanlog, x$sdlog)} )
    d$conf = paste(round(d$meanlog,2),round(d$sdlog,2), sep=', ')
    l = unique(d$conf)
    d$conf = factor(d$conf, l)
    levels(d$conf) = paste( seq_along(l), l, sep=": " )

    xbreaks = 0:30
    xlabels = format_si((2^xbreaks)*4096, appendix="B")
    #print(xlabels)

    p <- ggplot(d, aes(x=x,y=y,color=conf)) +
      geom_line() + 
      scale_x_continuous(breaks=xbreaks, labels=xlabels) +
      scale_color_grey(name='layout #: mean,sd', start=0, end=0.8) + 
      theme_paper() +
      theme(legend.position=c(0.45,0.6)) +
      theme(axis.text.x=element_text(angle=90, hjust=1)) +
      xlab("Free Extent Size (log scale)") +
      ylab("Ratio") +
      theme(plot.margin = unit(c(0,0,0,0), "cm"))
    print(p)  

    #save_plot(p, 'lognormaldist', w=5, h=3.3)
}

main <- function()
{
    d = data.frame(meanlog=0, sdlog=1)
    
    d = rbind(d, c(log(2),1)) #1
    d = rbind(d, c(log(20),0.1)) 
    d = data.frame(meanlog=log(seq(2,21,length=5)), sdlog=seq(1,0.1,length=5))
    print(d)

    plot_dists(d)
}

main()

