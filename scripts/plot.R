rdmine <- function() 
{
	a = read.table("C:/Users/Jun/Dropbox/0-Research/0-PLFS/exp/indexexp.txt", header=T)
	return(a)
}

sme <- function()
{
    source("C:/Users/Jun/Dropbox/0-Research/0-metadata/src/metawalker/scripts/plot.R")
}

plot_exthist <- function(df, monitor_by=1)
{
    # in case of too many monitors, pick some of them
    monitors = levels(df$monitor_time) 
    monitors = monitors[seq(1, length(monitors), by=monitor_by)]
    df = subset(df, monitor_time %in% monitors)


    df$Ext_range =  paste(df$Extent_start, df$Extent_end, sep="-")
    
    df$finestart = df$start_num*df$start_unit

    mydf = ddply(df, .(finestart), head, n=1)
    mydf = arrange(mydf, finestart)
    sortedRange = as.character(mydf$Ext_range)
   

    # sort the factor
    df$Ext_range = factor(df$Ext_range, levels=sortedRange)

    p <- ggplot(df, aes(x=Ext_range, y=Percent, 
                        color=monitor_time,
                        group=monitor_time))+
        geom_line(alpha=3/3) +
        geom_jitter(size=5, alpha=3/3, position = position_jitter(height = 0, width = 0.3)) +
        ylab("Percent (fregment size/FS capacity)")+
        xlab("Extent Ranges")
    print(p)
}

plot_exthist_bar <- function(df, monitor_by=1, ptitle="PlotTitle", manjust=5, dotext=T)
{
    # in case of too many monitors, pick some of them
    monitors = levels(df$monitor_time) 
    monitors = monitors[seq(1, length(monitors), by=monitor_by)]
    df = subset(df, monitor_time %in% monitors)


    df$Ext_range =  paste(df$Extent_start, df$Extent_end, sep="-")
    
    df$finestart = df$start_num*df$start_unit

    mydf = ddply(df, .(finestart), head, n=1)
    mydf = arrange(mydf, finestart)
    sortedRange = as.character(mydf$Ext_range)
   
    df = ddply(df, .(Ext_range), pickandset, all_times=unique(df$monitor_time),
                                             col2set="Percent")

    # sort the factor
    df$Ext_range = factor(df$Ext_range, levels=sortedRange)
    df$Percentpos = df$Percent+manjust

    p <- ggplot(df, aes(x=Ext_range, y=Percent, 
                        color=monitor_time,
                        fill=monitor_time,
                        group=monitor_time))+
        #geom_line(alpha=3/3) +
        #geom_jitter(size=5, alpha=3/3, position = position_jitter(height = 0, width = 0.3)) +
        #geom_point(position='dodge')+
        geom_bar(position='dodge',stat='identity', drop=F)+
        ylab("Percent (fregment size/FS capacity)")+
        xlab("Extent Ranges")+
        ggtitle(ptitle) +
        facet_wrap(~jobid, ncol=2) +
        opts(axis.text.x=theme_text(angle=45, hjust=1))

    if ( dotext == T ) {
        p = p + geom_text(aes(label=Percent, x=Ext_range, y=Percentpos), 
                  angle=90, size=4, color='blue',
                  position=position_dodge(width=1))
    }
    print(p)
}

plot_exthist_bar_count <- function(df, monitor_by=1, ptitle="PlotTitle", manjust=0,
                                   dotext=T, mapstride=F, dfmapper=NULL)
{
    # in case of too many monitors, pick some of them
    monitors = levels(df$monitor_time) 
    monitors = monitors[seq(1, length(monitors), by=monitor_by)]
    df = subset(df, monitor_time %in% monitors)


    df$Ext_range =  paste(df$Extent_start, df$Extent_end, sep="-")
    
    df$finestart = df$start_num*df$start_unit

    mydf = ddply(df, .(finestart), head, n=1)
    mydf = arrange(mydf, finestart)
    sortedRange = as.character(mydf$Ext_range)
   

    df = ddply(df, .(Ext_range, jobid), pickandset, all_times=unique(df$monitor_time))

    # calc text position
    myymax = max( df$Free_extents, na.rm=T)
    txt_y_adust = myymax * 0.08 
    df$textypos = df$Free_extents+txt_y_adust + manjust
    # sort the factor
    df$Ext_range = factor(df$Ext_range, levels=sortedRange)

    if ( mapstride ) {
        df$jobid = mapvalues(df$jobid, from=dfmapper$jobid, to=dfmapper$wstride)
    }

    p <- ggplot(df, aes(x=Ext_range, y=Free_extents, 
                        color=monitor_time,
                        fill=monitor_time,
                        group=monitor_time))+
        #geom_line(alpha=3/3) +
        #geom_jitter(size=5, alpha=3/3, position = position_jitter(height = 0, width = 0.3)) +
        #geom_point(position='dodge')+
        geom_bar(position='dodge',stat='identity')+
        ylab("Number of free extents")+
        xlab("Extent Ranges") +
        #coord_cartesian(ylim=c(0,95000))+
        ggtitle(ptitle) + 
        facet_wrap(~jobid) +
        opts(axis.text.x=theme_text(angle=45, hjust=1))
        #scale_x_discrete(drop=F)

    if (dotext) {
        p = p + geom_text(aes(label=Free_extents, x=Ext_range, y=textypos), 
                  angle=90, size=2, color='blue',
                  position=position_dodge(width=1))
    }
    print(p)
}

mapstride <- function(df, dfmapper) 
{
    df$wstride = mapvalues(df$jobid, from=dfmapper$jobid, to=dfmapper$wstride)
    return(df)
}


pickandset <- function(df, all_times, col2set="Free_extents") {
    if ( nrow(df) == 0 ) {
        print("IT IS ZERO ROWS")
        return()
    }
    df.ret = df[, c('Ext_range', col2set, 'monitor_time', 'jobid')]
    missed_times_index = !(all_times %in% df.ret$monitor_time)
    missed_times = all_times[missed_times_index]

    if ( length( missed_times ) == 0 ) {
        # nothing missed
        return (df.ret)
    }

    df.missed = data.frame(monitor_time=missed_times)
    df.missed[,col2set]=0
    df.missed$Ext_range = df.ret$Ext_range[1]
    df.missed$jobid = df.ret$jobid[1]

    ret = rbind(df.ret, df.missed)
    return (ret)
}




plot_all <- function(df)
{
    #h3times = unique(df.h3$monitor_time)
    #h3times = h3times[1:9]
    #df.h3plot = subset(df.h3, monitor_time %in% h3times)
    #plot_exthist_bar(df.h3plot, monitor_by=1, ptitle="test 3")
    #windows()
    #plot_exthist_bar_count(df.h3plot, monitor_by=1, ptitle="test 3", manjust = 10000)

    plot_exthist_bar(df.h4, monitor_by=1, ptitle="test 4 (whole set)", dotext=F)
    windows()
    plot_exthist_bar(df.h4, monitor_by=15, ptitle="test 4 (sampled)", dotext=T)
    windows()
    plot_exthist_bar_count(df.h4, monitor_by=15, ptitle="test 4 (sampled)", dotext=T, manjust=10000)
    windows()
    plot_exthist_bar_count(df.h4, monitor_by=1, ptitle="test 4 (whole set)", dotext=F)
}


files2df <- function(dirpath)
{
    dflist = list()
    files = list.files(dirpath)
    for (f in files) {
        fpath = paste(dirpath, f, sep="/")
        fidx = sub("^.*\\.", "", f)
        dflist[[fidx]] = read.table(fpath, header=T)
    }
    #print (str(dflist))
    # put walkman config to all other df

    dfvec = c("_extstats", "_extstatssum", "_freefrag_sum",
              "_freefrag_hist", "_freeblocks", "_freeinodes",
              "_walkman_config")
    conf = dflist[['_walkman_config']][,c("hostname", "jobid", "nyears", "nseasons_per_year",
                                          "np", "ndir_per_pid", "nfile_per_dir", "nwrites_per_file",
                                          "wsize", "wstride", "startoff")]
    for ( dfname in dfvec[ dfvec!='_walkman_config'] ) {
        dflist[[dfname]] = merge(dflist[[dfname]], conf, by=c("jobid")) 
    }

    return (dflist)
}

plot_freefrag <- function(df)
{
    plot_exthist_bar(df)
    plot_exthist_bar_count(df)
            #_extstats: how many metadata/data blocks per file, and more
            #_extstatssum: total numbers of metadata/data blocks for
                #the whole file system
            #_freefrag_sum: average size of extent....
            #_freefrag_hist: the histgram of extents
            #_freeblocks: the start and end block number of each free extent
            #_freeinodes: free inode number ranges
        #In *.cols:
            #_walkman_config: the config of this run (system and workload)

}

# seecol can be fs_nmetablocks or fs_datablocks
plot_extstatssum <- function(df, seecol)
{
    df$wstride = factor(df$wstride)
    p <- ggplot(df, aes_string(x="wstride", y=seecol, fill="monitor_time")) +
        geom_bar(stat='identity', position='dodge', drop=F) +
        #geom_text(aes(label=fs_nmetablocks), position=position_dodge(width=1))+
        scale_x_discrete(drop=F) 
    print(p)
}

main <- function() {
    #df = mylist[['_extstatssum']]
    #plot_extstatssum(df, "fs_nmetablocks")
    #windows()
    #plot_extstatssum(df, "fs_ndatablocks")

    #df = mylist[['_freefrag_sum']]
    #plot_extstatssum(df, 'Max_free_extent')

    innerfunc <- function() {
        print ("I am innerfunc\n")
    }
}

#################################################
#################################################
#################################################
#################################################
#################################################
# For wstride and wsize
# list.ss
plot_one_yvar <- function(df, seecol, n_per_jobid=10)
{
    df = ddply(df, .(jobid), head, n=n_per_jobid)
    #df$wstride = factor(df$wstride)
    df$wsize = factor(df$wsize)
    levels(df$wsize) = paste("WriteSize:", levels(df$wsize))
    p <- ggplot(df, aes_string(x="factor(wstride)", y=seecol, fill="monitor_time")) +
        geom_bar(stat='identity', position='dodge', drop=F) +
        #geom_text(aes(label=fs_nmetablocks), position=position_dodge(width=1))+
        scale_x_discrete(drop=F) +
        facet_wrap(~wsize) +
        xlab("Write stride")
    print(p)
}

plot_freefrag_sum <- function(df, n_per_jobid=10)
{
    df = ddply(df, .(jobid), head, n=n_per_jobid)

    df = melt(df, id=c("jobid", "monitor_time", "wsize", "wstride"),
                  measure=c(
                            "Avg_free_extent",
                            "Max_free_extent", 
                            "Blocksize",
                            "Total_blocks", 
                            "Free_blocks",
                            "Min_free_extent"
                            ))

    head(df)

    df$wstride = factor(df$wstride)
    levels(df$wstride) = paste("Stride:", levels(df$wstride)) 
    df$wsize = factor(df$wsize)
    levels(df$wsize) = paste("WSize:", levels(df$wsize))

    p <- ggplot(df, aes(x=variable, y=value, fill=monitor_time))+
            geom_bar(stat='identity', position='dodge') +
            scale_x_discrete(drop=F)+
            facet_wrap(wstride~wsize)+
            #opts(axis.text.x=theme_text(angle=45, hjust=1))
            theme(axis.text.x=element_text(angle=45,hjust=1))
    print(p)
}

ss_main <- function() 
{
    #list.ss = files2df("C:/Users/Jun/Dropbox/0-Research/0-metadata/datahub/results.h0.wsize.wstride")
    
    #df = list.ss[['_extstatssum']]
    #plot_one_yvar(df, "fs_ndatablocks", n_per_jobid=10)
    #windows()
    #plot_one_yvar(df, "fs_nmetablocks", n_per_jobid=10)

    #df = list.ss[['_freefrag_sum']]
    #plot_freefrag_sum(df, n_per_jobid=100)

    df = list.ss[['_freefrag_hist']]
    ss_plot_exthist_bar(df, dotext=F)
}

# input should be _free_fraghist
ss_plot_exthist_bar <- function(df, monitor_by=1, ptitle="PlotTitle", manjust=5, dotext=T)
{
    # in case of too many monitors, pick some of them
    monitors = levels(df$monitor_time) 
    monitors = monitors[seq(1, length(monitors), by=monitor_by)]
    df = subset(df, monitor_time %in% monitors)

    df$Ext_range =  paste(df$Extent_start, df$Extent_end, sep="-")
    
    df$finestart = df$start_num*df$start_unit
    mydf = ddply(df, .(finestart), head, n=1)
    mydf = arrange(mydf, finestart)
    sortedRange = as.character(mydf$Ext_range)
   
    # sort the factor
    df$Ext_range = factor(df$Ext_range, levels=sortedRange)
    df$Percentpos = df$Percent+manjust

    df = ddply(df, .(jobid, monitor_time), ss_pickandset, all_exts=unique(df$Ext_range),
                                             col2set="Percent")
    
    df$wstride = factor(df$wstride)
    df$wsize = factor(df$wsize)

    # clearer annotation
    levels(df$wstride) = paste("Stride:", levels(df$wstride))
    levels(df$wsize) = paste("Size:", levels(df$wsize))
    print (summary(df$wsize))
    p <- ggplot(df, aes(x=Ext_range, y=Percent, 
                        color=monitor_time,
                        fill=monitor_time,
                        group=monitor_time))+
        #geom_line(alpha=3/3) +
        #geom_jitter(size=5, alpha=3/3, position = position_jitter(height = 0, width = 0.3)) +
        #geom_point(position='dodge')+
        geom_bar(position='dodge',stat='identity', drop=F)+
        ylab("Percent (fregment size/FS capacity)")+
        xlab("Extent Ranges")+
        ggtitle(ptitle) +
        facet_grid(wsize~wstride)+
        theme(axis.text.x=element_text(angle=45, hjust=1))


    if ( dotext == T ) {
        p = p + geom_text(aes(label=Percent, x=Ext_range, y=Percentpos), 
                  angle=90, size=4, color='blue',
                  position=position_dodge(width=1))
    }
    print(p)
}

# df has same ext_range and jobid
# for one monitor_time of a particular jobid, there should
# be only one row for one extent range
# WARNING: in the return of this function, except for 
# jobid, monitor_time, Ext_range, col2set, other colums
# are NOT valid.
ss_pickandset <- function(df, all_exts, col2set="Free_extents") {
    if ( nrow(df) == 0 ) {
        print("IT IS ZERO ROWS")
        return()
    }
    missed_exts_index = !(all_exts %in% df$Ext_range)
    missed_exts = all_exts[missed_exts_index]

    if ( length( missed_exts ) == 0 ) {
        # nothing missed
        return (df)
    }

    nrows.missed = length(missed_exts)
    df.missed =  df[rep(1, nrows.missed), ]
    df.missed[,col2set]=0
    df.missed$Ext_range = missed_exts

    ret = rbind(df, df.missed)
    return (ret)
}


