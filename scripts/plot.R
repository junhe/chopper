require(ggplot2)
require(reshape)
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
    #require(sqldf)
    dflist = list()
    files = list.files(dirpath)
    print(files)
    dfvec=NULL
    for (f in files) {
        fpath = paste(dirpath, f, sep="/")
        print(fpath)
        fidx = sub("^.*\\.", "", f)
        dfvec = append(dfvec, fidx)
        dflist[[fidx]] = read.table(fpath, header=T)
    }
    #print (str(dflist))
    # put walkman config to all other df

    #dfvec = c("_extlist", "_extstats", "_extstatssum", "_freefrag_sum",
              #"_freefrag_hist", "_freeblocks", "_freeinodes",
              #"_walkman_config")
    #conf = dflist[['_walkman_config']][,c("hostname", "jobid", "nyears", "nseasons_per_year",
                                          #"np", "ndir_per_pid", "nfile_per_dir", "nwrites_per_file",
                                          #"wsize", "wstride", "startoff")]
    
    conf = dflist[['_walkman_config']]

    for ( dfname in dfvec[ dfvec!='_walkman_config'] ) {
        print( paste( "Merging", "......." ) )
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
    df$ypos = df[,seecol]*0.8
    p <- ggplot(df, aes_string(x="factor(wstride)", y=seecol, fill="monitor_time")) +
        geom_bar(stat='identity', position='dodge', drop=F) +
        geom_text(aes_string(label=seecol, y="ypos"), position=position_dodge(width=1), angle=90)+
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

# plot the relation between filepath and number of metablocks
ss_plot_meta_file <- function(df, n_per_jobid)
{
    df = ddply(df, .(jobid, filepath), head, n=n_per_jobid)
    

    df = subset(df, wsize==1 & monitor_time=='year00009.season00003')
    print (df)
    df$wstride = factor(df$wstride)
    df$wsize = factor(df$wsize)
    # clearer annotation
    levels(df$wstride) = paste("Stride:", levels(df$wstride))
    levels(df$wsize) = paste("Size:", levels(df$wsize))

    p <- ggplot(df, aes(x=filepath, y=n_metablock, fill=monitor_time), drop=F) +
        geom_bar(stat='identity', position='dodge')+
        facet_grid(wstride~wsize)+
        theme(axis.text.x=element_text(angle=45,hjust=1))
    print(p)
}

ss_main <- function() 
{
    #list.ss = files2df("C:/Users/Jun/Dropbox/0-Research/0-metadata/datahub/results.h0.wsize.wstride")
   

    #df = list.ss[['_extstats']]
    #ss_plot_meta_file(df, n_per_jobid=100)

    #########
    df = list.ss[['_extstatssum']]
    plot_one_yvar(df, "fs_ndatablocks", n_per_jobid=5)
    windows()
    plot_one_yvar(df, "fs_nmetablocks", n_per_jobid=5)
    df$Number.Of.Medadata.Block.Per.Data.Block = with(df, fs_nmetablocks/fs_ndatablocks)
    windows()
    plot_one_yvar(df, "Number.Of.Medadata.Block.Per.Data.Block", n_per_jobid=10)

    # df has the same jobid
    get_ncur_files <- function(df)
    {
        df = arrange(df, monitor_time)
        n = nrow(df)
        df$season = (1:n)-1
        tmp = with(df[1,], np*ndir_per_pid*nfile_per_dir*nwrites_per_file)
        df$n_cur_files = tmp * 3
        df$n_cur_files[1] = tmp
        df$n_cur_files[2] = tmp*2
        return (df)
    }
    df = ddply(df, .(jobid), get_ncur_files)
    df$Number.Of.Metadata.Block.Per.Write = 
        with(df, fs_nmetablocks/n_cur_files)
    windows()
    plot_one_yvar(df, "Number.Of.Metadata.Block.Per.Write", n_per_jobid=10)

    #########
    #df = list.ss[['_freefrag_sum']]
    #plot_freefrag_sum(df, n_per_jobid=100)

    #########
    #df = list.ss[['_freefrag_hist']]
    ##ss_plot_exthist_bar(df, dotext=F)
    #ss_plot_exthist_bar(df, dotext=F, col2set="Free_extents")

}

# for results with extlist
plot_physical_blocks <- function(df, nseasons)
{
    tms = levels(df$monitor_time)
    pickedtms = head(tms, n=nseasons)
    
    df = subset(df, monitor_time %in% pickedtms)# & wsize==1 & wstride==4096 )
    
    df$rowid = row.names(df)
    rowsize = 1000
    df = ddply(df, .(rowid), ddply_trans_wide, rowsize=rowsize)
    df$y = df$y *rowsize

    # clearer annotation
    df$wstride = factor(df$wstride)
    df$wsize = factor(df$wsize)
    levels(df$wstride) = paste("Stride:", levels(df$wstride))
    levels(df$wsize) = paste("Size:", levels(df$wsize))
    p <- ggplot(df, aes()) +
        geom_segment(aes(x=x.start, xend=x.end+1,
                         y=y, yend=y,
                         color=filepath), size=1)+
        facet_grid(wstride~wsize) +
        theme( axis.text.x = element_blank() ) +
        xlab("") +
        ylab("block number") +
        ylim(c(0, 65535))
    print (p)
}

# The input has to be only one row
# It splits a long segment to multiple
# smaller segments.
ddply_trans_wide <- function(df, rowsize=10000)
{
    start.row.y = floor(df$Physical_start/rowsize)
    start.row.x = df$Physical_start%%rowsize
    
    end.row.y = floor(df$Physical_end/rowsize)
    end.row.x = df$Physical_end%%rowsize
    
    if (end.row.y == start.row.y) {
        df$x.start = start.row.x
        df$x.end = end.row.x

        df$y = start.row.y
        return (df)
    } else {
        tp = head(df, n=1) 
        tp$x.start = 0
        tp$x.end = 0
        tp$y = 0
        
        # for start row
        r.start = tp
        r.start$x.start = start.row.x
        r.start$x.end = rowsize 
        r.start$y = start.row.y
        
        # for end row
        r.end = tp
        r.end$x.start = 0
        r.end$x.end = end.row.x
        r.end$y = end.row.y

        df.ret = rbind(r.start, r.end)
        if ( end.row.y > start.row.y + 1 ) {
            # there's line(s) in the middle
            for ( i in (start.row.y+1):(end.row.y-1)){
                r.mid = tp
                r.mid$x.start = 0
                r.mid$x.end = rowsize
                r.mid$y = i

                df.ret = rbind(df.ret, r.mid)
            }
        }
        return(df.ret)
    }

}

# The input df is the free blocks of a whole
# file system got from dumpe2fs
layout_score_of_freeblocks <- function(df)
{
    df$count = df$end - df$start + 1
    total = sum(df$count)
    layout_score = (total - nrow(df))/(total - 1)
    return (layout_score)
}

freeblock_hist <- function(df)
{
    n_jobs = 4
    n_monitors = 4
    
    joblist = unique(df$jobid)
    pickedjobs = head(joblist, n=n_jobs)

    monitorlist = df$monitor_time
    pickedmon = head(monitorlist, n=n_monitors)

    df = subset(df, jobid %in% pickedjobs)
    df = subset(df, monitor_time %in% pickedmon)

    df$size = df$end - df$start + 1
    p <- ggplot(df, aes(x=size)) +
        #geom_histogram() + 
        geom_density() +
        facet_grid(jobid~monitor_time)
    print(p)
}


layoutScoreOfAFile <- function(df)
{
}

aggregateLayoutScoreOfFS <- function(df)
{
    ddply(df, .(jobid, monitor_time, filepath), layoutScoreOfAFile)
}

ss_main2 <- function() 
{
    #list.ss2 <<- files2df("C:/Users/Jun/Dropbox/0-Research/0-metadata/datahub/h0")
   

    #df = list.ss2[['_freeblocks']]
    #freeblock_hist(df)
    #print ( layout_score_of_freeblocks(df) )

    df = list.ss2[['_extlist']]
    #plot_physical_blocks(df, 1)
    aggregateLayoutScoreOfFS(df)


    #df = list.ss[['_extstats']]
    #ss_plot_meta_file(df, n_per_jobid=100)

    #########
    #df = list.ss[['_extstatssum']]
    #plot_one_yvar(df, "fs_ndatablocks", n_per_jobid=5)
    #windows()
    #plot_one_yvar(df, "fs_nmetablocks", n_per_jobid=5)
    #df$Number.Of.Medadata.Block.Per.Data.Block = with(df, fs_nmetablocks/fs_ndatablocks)
    #windows()
    #plot_one_yvar(df, "Number.Of.Medadata.Block.Per.Data.Block", n_per_jobid=10)

    ## df has the same jobid
    #get_ncur_files <- function(df)
    #{
        #df = arrange(df, monitor_time)
        #n = nrow(df)
        #df$season = (1:n)-1
        #tmp = with(df[1,], np*ndir_per_pid*nfile_per_dir*nwrites_per_file)
        #df$n_cur_files = tmp * 3
        #df$n_cur_files[1] = tmp
        #df$n_cur_files[2] = tmp*2
        #return (df)
    #}
    #df = ddply(df, .(jobid), get_ncur_files)
    #df$Number.Of.Metadata.Block.Per.Write = 
        #with(df, fs_nmetablocks/n_cur_files)
    #windows()
    #plot_one_yvar(df, "Number.Of.Metadata.Block.Per.Write", n_per_jobid=10)

    #########
    #df = list.ss[['_freefrag_sum']]
    #plot_freefrag_sum(df, n_per_jobid=100)

    #########
    #df = list.ss[['_freefrag_hist']]
    ##ss_plot_exthist_bar(df, dotext=F)
    #ss_plot_exthist_bar(df, dotext=F, col2set="Free_extents")

}




# input should be _free_fraghist
ss_plot_exthist_bar <- function(df, monitor_by=1, ptitle="PlotTitle", manjust=5, dotext=T, col2set="Percent")
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
                                             col2set=col2set)
    
    df$wstride = factor(df$wstride)
    df$wsize = factor(df$wsize)
    # clearer annotation
    levels(df$wstride) = paste("Stride:", levels(df$wstride))
    levels(df$wsize) = paste("Size:", levels(df$wsize))

    p <- ggplot(df, aes_string(x="Ext_range", y=col2set, 
                        color="monitor_time",
                        fill="monitor_time",
                        group="monitor_time"))+
        #geom_line(alpha=3/3) +
        #geom_jitter(size=5, alpha=3/3, position = position_jitter(height = 0, width = 0.3)) +
        #geom_point(position='dodge')+
        geom_bar(position='dodge',stat='identity', drop=F)+
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



#####################################################
#####################################################
#    search stride and nwrites


sw_main <- function() 
{
    #list.sw <<- files2df("C:/Users/Jun/Dropbox/0-Research/0-metadata/datahub/h1.stride.nwrite")
   
    df = list.sw[['_extstatssum']]
    sw_plot_one_yvar(df, "fs_ndatablocks", n_per_jobid=20)
    windows()
    sw_plot_one_yvar(df, "fs_nmetablocks", n_per_jobid=20)
    df$Number.Of.Medadata.Block.Per.Data.Block = with(df, fs_nmetablocks/fs_ndatablocks)
    windows()
    sw_plot_one_yvar(df, "Number.Of.Medadata.Block.Per.Data.Block", n_per_jobid=20)

}

sw_plot_one_yvar <- function(df, seecol, n_per_jobid=10, dotext=F)
{
    df = ddply(df, .(jobid), head, n=n_per_jobid)
    #df$wstride = factor(df$wstride)
    df$nwrites_per_file = factor(df$nwrites_per_file)
    levels(df$nwrites_per_file) = paste("NWritesPerFile:", levels(df$nwrites_per_file))
    print(head(df))
    df$ypos = df[,c(seecol)]*0.8
    print("here i am")
    p <- ggplot(df, aes_string(x="factor(wstride)", y=seecol, fill="monitor_time")) +
        geom_bar(stat='identity', position='dodge', drop=F) +
        scale_x_discrete(drop=F) +
        facet_wrap(~nwrites_per_file) +
        xlab("Write stride")
    if ( dotext ) {
        p = p + 
            geom_text(aes_string(label=seecol, y="ypos"), position=position_dodge(width=1), angle=90)
    }
    print(p)
}


####################
# search for the right alpha and beta

generateFrags <- function(alpha, beta, count, sum_lim)
{
    l = rbeta(count, alpha, beta)
    windows()
    p = qplot(l)+xlim(c(0,1))+
        ggtitle( paste(alpha, beta))
    print (p)

    expl=2^(17*l)
    windows()
    p = qplot(expl*4096/(1024))+xlim(c(0, 2^17))+
        ggtitle( paste(alpha, beta))
    print (p)
    
    sm = sum(expl)
    fragsz = floor(expl*sum_lim/sm)
    fragsz = sort(fragsz)
    windows()
    p = qplot(fragsz*4096/1024)+
        ggtitle( paste(alpha, beta))
    print (p)
}

frag_main <- function()
{
    #generateFrags(alpha=2,
                  #beta=5,
                  #count=4096,
                  #sum_lim=3*1024*1024*1024/4096)
    print ("entering fragmain")
    a=c(10, 2,  5, 2, 5)
    b=c(2,  10, 2, 5, 5)
    for (i in 1:5) {
        tmp = generateFragsV2(alpha=a[i],
                  beta=b[i],
                  sum_lim=3*1024*1024*1024/4096,
                  tolerance=0.05)
    }
}

generateFragsV2 <- function(alpha, beta, sum_lim, tolerance)
{
    print("entering v2")
    print(c(alpha, beta))
    fragsizes = c()
    betas = c()
    trialslimit = 100
    while (1) {
        k = rbeta(1, alpha, beta)
        betas = append(betas, k)
        sz = floor(2^(15*k))
        fragsizes = append(fragsizes, sz)
        szsum = sum(fragsizes)
        if ( szsum >= sum_lim*(1-tolerance) &&
             szsum <= sum_lim*(1+tolerance) ) 
        {
            print ("NICE reach within tolerance")
            print (paste("Sum:", szsum))
            print (paste("target:", sum_lim))
            print (paste("count:", length(fragsizes)))
            print (summary(fragsizes))
            p = qplot(betas)+xlim(c(0,1))+ggtitle(paste(alpha, beta))
            windows()
            print (p)
            p = qplot(fragsizes*4096/1024, binwidth=64)+ggtitle(paste(alpha, beta))+xlab("KB")+
                scale_x_continuous(breaks=seq(0,50000, by=5000))+
                theme(axis.text.x=element_text(angle=45,hjust=1))
            windows()
            print (p)
            return (fragsizes)
        } else if ( szsum > sum_lim*(1+tolerance) ) {
            print ("Damn.................. failed to reach target within tolerance")
            return (NULL)
        }
    }
}

#######################################
## With fragment distribution
##

pick_by_stride <- function(keys, stride) 
{
    n = length(keys)
    selects = seq(1,n,by=stride)
    keys = sort(keys)
    return (keys[selects])
}

fdist_free_space_hist <- function(df)
{
    df$Free_Space_Dist_ID = paste("alpha:", df$alpha, ",", "beta:", df$beta, sep="")
    df$Free_Space.Dist_ID = factor(df$Free_Space_Dist_ID)
    df$Workload_ID = paste("np:", df$np, ",",
                           "ndir_per_pid:", df$ndir_per_pid, ",",
                           "nfile_per_dir:", df$nfile_per_dir, ",",
                           "nwrites_per_file:", df$nwrites_per_file, ",",
                           "wsize:", df$wsize, ",",
                           "wstride:", df$wstride, ",",
                           "startoff:", df$startoff,
                           sep="")
    df$Workload_ID = factor(df$Workload_ID)

    # pick free spaces
    nFree_Space_Dist_ID = 3 
    distids = unique(df$Free_Space_Dist_ID)
    print(distids)
    picked_distids = head(distids, n=nFree_Space_Dist_ID)
    #df = subset(df, Free_Space_Dist_ID %in% picked_distids)
    df = subset(df, Free_Space_Dist_ID %in% c("alpha:2,beta:5", "alpha:5,beta:2"))

    # pick workloads
    nWorkload_ID = 10 
    wlids = unique(df$Workload_ID)
    print(wlids)
    picked_wlids = head(wlids, n=nWorkload_ID)
    df = subset(df, Workload_ID %in% picked_wlids)

    # pick monitors
    pickedMons = pick_by_stride(unique(df$monitor_time), stride=5)
    df = subset(df, monitor_time %in% pickedMons)

    df$Fragment_Block_Count = df$end - df$start + 1
    df$Fragment_Log2Size = log(df$Fragment_Block_Count*4096, 2)
    
    print(head(df))
    
    p = ggplot(df, aes(
                       x=Fragment_Log2Size,
                       #x=Fragment_Block_Count, 
                       color=monitor_time
                       )) +
        #geom_histogram(position='dodge') +
        geom_density()+
        facet_grid(Free_Space_Dist_ID~Workload_ID)+
        scale_x_continuous(breaks=seq(12, 27, by=2),
                           labels=(2^seq(12, 27, by=2)/1024))+
        xlab("Fragment Size(KB)")
    print(p)
}

fdist_meta_data_blocks <- function(df)
{
    df$Free_Space_Dist_ID = paste("alpha:", df$alpha, ",", "beta:", df$beta, sep="")
    df$Free_Space.Dist_ID = factor(df$Free_Space_Dist_ID)
    df$Workload_ID = paste("np", df$np, ",",
                           "nd", df$ndir_per_pid, ",",
                           "nf", df$nfile_per_dir, ",",
                           "nw", df$nwrites_per_file, ",",
                           "ws", df$wsize, ",",
                           "wst", df$wstride, ",",
                           "so", df$startoff,
                           sep="")
    df$Workload_ID = factor(df$Workload_ID)
    print("before ggplot")
    p = ggplot(df, aes(
                       x=monitor_time,
                       #y=fs_nmetablocks,
                       y=fs_ndatablocks,
                       color=monitor_time,
                       fill=monitor_time
                       )) +
        #geom_histogram(position='dodge') +
        geom_bar(stat="identity", position='dodge')+
        facet_grid(Free_Space_Dist_ID~Workload_ID)+
        xlab("Time")
    print("after ggplot")
    print(p)
}

# This set of data is generated on h6.metawalker.plfs.
# It has uses differnt beta distributions to generate
# fragmentations and it has various workloads.
fdist_main <- function()
{
    #list.fdist <<- files2df("C:/Users/Jun/Documents/Workdir/h6.tar/h6")
    #print(str(list.fdist))

    #df = list.fdist[['_freeblocks']]
    #fdist_free_space_hist(df)

    df = list.fdist[['_extstatssum']]
    #head(df)
    fdist_meta_data_blocks(df)
    print(df$fs_nmetablocks)
}

##########################################
## h6 checkpoint 00
##
h6ck00_main <- function()
{
    #list.h6ck00 <<- files2df("C:/Users/Jun/Documents/Workdir/h6.chkpoint00")
    #print(str(list.h6ck00))
    #save(list.h6ck00, file="list.h6ck00._freeblocks.Rdata")

    df = list.h6ck00[['_freeblocks']]
    fdist_free_space_hist(df)
}













