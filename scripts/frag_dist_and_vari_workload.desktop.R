# This set of functions if for tests conducted in Sept 2nd.
# In these test, the file system fragmentation is setted as
# beta distribution, the parameters of workload is same as 
# before. The only difference between this and result data before
# is that this one has framentation configuration.
require(ggplot2)
require(reshape)



rdmine <- function() 
{
	a = read.table("C:/Users/Jun/Dropbox/0-Research/0-PLFS/exp/indexexp.txt", header=T)
	return(a)
}

sme <- function()
{
    source("/u/j/h/jhe/workdir/metawalker/scripts/frag_dist_and_vari_workload.desktop.R")
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

pick_by_stride <- function(keys, stride) 
{
    n = length(keys)
    selects = seq(1,n,by=stride)
    keys = sort(keys)
    return (keys[selects])
}

# You speicify either df or rfile. 
# rfile has to have a data frame named df
fdist_free_space_hist2 <- function(df=NULL, rfile="")
{
    if ( is.null(df) ) {
        load(file=rfile)#, globalenv())
    } else {
        # pick monitors
        pickedMons = pick_by_stride(unique(df$monitor_time), stride=1)
        df = subset(df, monitor_time %in% pickedMons)

        # build factor
        df$Free_Space_Dist_ID = paste("alpha:", df$alpha, ",", "beta:", df$beta, sep="")
        df$Free_Space.Dist_ID = factor(df$Free_Space_Dist_ID)
        df$Workload_ID = paste("np", df$np, ",",
                               "nd", df$ndir_per_pid, ",",
                               "nf", df$nfile_per_dir, ",",
                               "nw", df$nwrites_per_file, "\n",
                               "ws", df$wsize, ",",
                               "wst", df$wstride, ",",
                               "so", df$startoff,
                               sep="")
        df$Workload_ID = factor(df$Workload_ID)

        # pick free spaces
        nFree_Space_Dist_ID = 6 
        distids = unique(df$Free_Space_Dist_ID)
        print(distids)
        picked_distids = head(distids, n=nFree_Space_Dist_ID)
        df = subset(df, Free_Space_Dist_ID %in% picked_distids)

        # fragment data calculation
        df$Fragment_Block_Count = df$end - df$start + 1
        df$Fragment_Log2Size = log(df$Fragment_Block_Count*4096, 2)
        
        #print(summary(df$Workload_ID))
        save(df, file="h7check01.freespacehist.Rdata")
        return(NULL)
    }

    lvls = unique( as.character(df$Workload_ID) )
    df$Workload_ID = factor(df$Workload_ID, levels=lvls)

    mlvl = length(levels(df$Workload_ID))
    ranges = list( 1:11, 12:22, 23:33) 

    for (myrng in ranges) {
        print(myrng)
        pickedWkload = levels(df$Workload_ID)[intersect(myrng, 1:mlvl)]
        print(pickedWkload)
        dfp = subset(df, Workload_ID %in% pickedWkload)

        p = ggplot(dfp, aes(
                           x=Fragment_Log2Size,
                           #x=Fragment_Block_Count, 
                           color=monitor_time
                           )) +
            geom_freqpoly(binwidth=1)+
            #geom_histogram(aes(fill=monitor_time), position='dodge') +
            #geom_density()+
            facet_grid(Free_Space_Dist_ID~Workload_ID)+
            scale_x_continuous(breaks=seq(12, 28, by=2),
                               labels=(2^seq(12, 28, by=2)/1024))+
            xlab("Fragment Size(KB)")+
            theme(axis.text.x=element_text(angle=45,hjust=1))+
            scale_y_log10(limits=c(0.001, 1e6))
        windows()
        print(p)
    }
}


fdist_free_space_hist_E <- function(df)
{
    # pick monitors
    #pickedMons = pick_by_stride(unique(df$monitor_time), stride=1)
    #df = subset(df, monitor_time %in% pickedMons)
    df = subset(df, 
                    alpha == 5 & 
                    beta == 5 &
                    np == 8 &
                    ndir_per_pid == 4 &
                    nfile_per_dir == 16 &
                    nwrites_per_file == 4096 &
                    wsize == 128 &
                    wstride == 256 & 
                    startoff == 0) 

    df$Free_Space_Dist_ID = paste("alpha:", df$alpha, ",", "beta:", df$beta, sep="")
    df$Free_Space.Dist_ID = factor(df$Free_Space_Dist_ID)
    df$Workload_ID = paste("np", df$np, ",",
                           "nd", df$ndir_per_pid, ",",
                           "nf", df$nfile_per_dir, ",",
                           "nw", df$nwrites_per_file, "\n",
                           "ws", df$wsize, ",",
                           "wst", df$wstride, ",",
                           "so", df$startoff,
                           sep="")
    df$Workload_ID = factor(df$Workload_ID)

    # pick free spaces
    nFree_Space_Dist_ID = 6 
    distids = unique(df$Free_Space_Dist_ID)
    print(distids)
    picked_distids = head(distids, n=nFree_Space_Dist_ID)
    df = subset(df, Free_Space_Dist_ID %in% picked_distids)

    # pick workloads
    nWorkload_ID = 20 
    wlids = unique(df$Workload_ID)
    print(wlids)
    picked_wlids = head(wlids, n=nWorkload_ID)
    df = subset(df, Workload_ID %in% picked_wlids)


    df$Fragment_Block_Count = df$end - df$start + 1
    df$Fragment_Log2Size = log(df$Fragment_Block_Count*4096, 2)
    
    print(head(df))
    
    p = ggplot(df, aes(
                       x=Fragment_Log2Size,
                       #x=Fragment_Block_Count, 
                       color=monitor_time
                       )) +
        geom_freqpoly(binwidth=1)+
        #geom_histogram(aes(fill=monitor_time), position='dodge') +
        #geom_density()+
        facet_grid(Free_Space_Dist_ID~Workload_ID)+
        scale_x_continuous(breaks=seq(12, 28, by=2),
                           labels=(2^seq(12, 28, by=2)/1024))+
        xlab("Fragment Size(KB)")+
        theme(axis.text.x=element_text(angle=45,hjust=1))+
        scale_y_log10(limits=c(0.001, 1e6))
    print(p)
}



fdist_free_space_hist <- function(df)
{
    # pick monitors
    pickedMons = pick_by_stride(unique(df$monitor_time), stride=1)
    df = subset(df, monitor_time %in% pickedMons)


    df$Free_Space_Dist_ID = paste("alpha:", df$alpha, ",", "beta:", df$beta, sep="")
    df$Free_Space.Dist_ID = factor(df$Free_Space_Dist_ID)
    df$Workload_ID = paste("np", df$np, ",",
                           "nd", df$ndir_per_pid, ",",
                           "nf", df$nfile_per_dir, ",",
                           "nw", df$nwrites_per_file, "\n",
                           "ws", df$wsize, ",",
                           "wst", df$wstride, ",",
                           "so", df$startoff,
                           sep="")
    df$Workload_ID = factor(df$Workload_ID)

    # pick free spaces
    nFree_Space_Dist_ID = 6 
    distids = unique(df$Free_Space_Dist_ID)
    print(distids)
    picked_distids = head(distids, n=nFree_Space_Dist_ID)
    df = subset(df, Free_Space_Dist_ID %in% picked_distids)

    # pick workloads
    nWorkload_ID = 20 
    wlids = unique(df$Workload_ID)
    print(wlids)
    picked_wlids = head(wlids, n=nWorkload_ID)
    df = subset(df, Workload_ID %in% picked_wlids)


    df$Fragment_Block_Count = df$end - df$start + 1
    df$Fragment_Log2Size = log(df$Fragment_Block_Count*4096, 2)
    
    print(head(df))
    
    p = ggplot(df, aes(
                       x=Fragment_Log2Size,
                       #x=Fragment_Block_Count, 
                       color=monitor_time
                       )) +
        geom_freqpoly(binwidth=1)+
        #geom_histogram(aes(fill=monitor_time), position='dodge') +
        #geom_density()+
        facet_grid(Free_Space_Dist_ID~Workload_ID)+
        scale_x_continuous(breaks=seq(12, 28, by=2),
                           labels=(2^seq(12, 28, by=2)/1024))+
        xlab("Fragment Size(KB)")+
        theme(axis.text.x=element_text(angle=45,hjust=1))+
        scale_y_log10()
    print(p)
}

fdist_meta_data_blocks <- function(df)
{

    # pick monitors
    pickedMons = pick_by_stride(unique(df$monitor_time), stride=1)
    df = subset(df, monitor_time %in% pickedMons)

    df$Free_Space_Dist_ID = paste("alpha:", df$alpha, ",", "beta:", df$beta, sep="")
    df$Free_Space.Dist_ID = factor(df$Free_Space_Dist_ID)
    df$Workload_ID = paste("np", df$np, ",",
                           "nd", df$ndir_per_pid, ",",
                           "nf", df$nfile_per_dir, ",",
                           "nw", df$nwrites_per_file, "\n",
                           "ws", df$wsize, ",",
                           "wst", df$wstride, ",",
                           "so", df$startoff,
                           sep="")
    df$Workload_ID = factor(df$Workload_ID)


    p = ggplot(df, aes(
                       x=monitor_time,
                       y=fs_nmetablocks,
                       #y=fs_ndatablocks,
                       fill=monitor_time
                       )) +
        #geom_histogram(position='dodge') +
        geom_bar(stat="identity", position='dodge')+
        geom_text(aes(label=fs_nmetablocks, y=fs_nmetablocks), 
                    position=position_dodge(width=1),
                  size=4, angle=90)+
        facet_grid(Free_Space_Dist_ID~Workload_ID)+
        theme(axis.text.x=element_text(angle=45,hjust=1))+
        #theme(strip.text.x=element_text(size=5))+
        xlab("Time")
    print("after ggplot")
    print(p)
}

df_filter <- function(df, p_np, p_nd, p_nf, p_nw, p_ws, p_wst, p_so, p_alpha, p_beta, p_monitor_time) 
{
    df = subset(df, 
                    monitor_time %in% p_monitor_time &
                    alpha == p_alpha & 
                    beta == p_beta &
                    np == p_np &
                    ndir_per_pid == p_nd &
                    nfile_per_dir == p_nf &
                    nwrites_per_file == p_nw &
                    wsize == p_ws &
                    wstride == p_wst & 
                    startoff == p_so 
                    )
    return (df)
}



# for results with extlist
plot_physical_blocks <- function(df, nseasons)
{
    tms = unique(as.character(df$monitor_time))
    pickedtms = head(tms, n=nseasons)
    
    df = subset(df, monitor_time %in% pickedtms)# & wsize==1 & wstride==4096 )
    
    df$rowid = row.names(df)
    rowsize = 1000
    df = ddply(df, .(rowid), ddply_trans_wide, rowsize=rowsize)
    df$y = df$y *rowsize

    df$filepath = factor( df$filepath, levels=sample(levels(df$filepath)) )

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
        xlab(paste("x range:", rowsize, sep="")) +
        ylab("block number") +
        ylim(c(0, 1.1e6))
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

# the input df should be 
lookat_one_file <- function()
{
    dfglb <<- df_filter(list.h7check01[['_extlist']], 
            p_np=4, p_nd=4, p_nf=4, p_nw=1024, 
            p_ws=4096, p_wst=4096, p_so=0, p_alpha=2, p_beta=5,
            p_monitor_time='year00001.season00000') 

    print(c("max level summary", summary(dfglb$Max_level)))

    plot_physical_blocks(dfglb, 100)
    return()
    
    tmp = subset(dfglb, Max_level > 0)
    print(nrow(tmp))
    plot_physical_blocks(tmp, 1)
    return ()


    firstfile = tmp$filepath[1]
    fileext = subset(dfglb, filepath == firstfile)
    print(fileext[,2:11])
    #plot_physical_blocks(fileext, 1)
}

lookat_one_file_A <- function()
{
    dfglb <<- df_filter(list.h7check01[['_extlist']], 
            p_np=4, p_nd=4, p_nf=4, p_nw=1024, 
            p_ws=4096, p_wst=4096, p_so=0, p_alpha=2, p_beta=5,
            p_monitor_time='year00999.season00999') 
    print(c('nrow:', nrow(dfglb)))
    print(head(dfglb))

    print(c("Max_level summary\n",summary(dfglb$Max_level)))
    #return(NULL)

    #selectedfiles = sample(unique(as.character(dfglb$filepath)), 100)
    #plot_physical_blocks(subset(dfglb, filepath %in% selectedfiles), 1)
    plot_physical_blocks(dfglb, 1)
    return()
    
    tmp = subset(dfglb, Max_level > 0)
    print(nrow(tmp))
    filepaths = unique(as.character(tmp$filepath))
    print(c("number of files has > 0 levels:", length(filepaths)))
    #selectedfiles = sample(filepaths, 100)
    #plot_physical_blocks(subset(tmp, filepath %in% selectedfiles), 1)
    plot_physical_blocks(tmp, 1)
    print("i am new")
    return ()


    samplefile = sample(tmp$filepath, 1)
    print(samplefile)
    fileext = subset(dfglb, filepath == samplefile)
    print(summary(dfglb$filepath))
    print(fileext[,2:11])
    plot_physical_blocks(fileext, 1)
}



lookat_one_file_B <- function()
{
    dfglb <<- df_filter(list.h7check01[['_extlist']], 
            p_np=8, p_nd=8, p_nf=16, p_nw=4096, 
            p_ws=64, p_wst=64, p_so=0, p_alpha=2, p_beta=5,
            p_monitor_time='year00001.season00000') 

    print(c("Max_level summary\n",summary(dfglb$Max_level)))

    selectedfiles = sample(unique(as.character(dfglb$filepath)), 100)
    plot_physical_blocks(subset(dfglb, filepath %in% selectedfiles), 1)
    #plot_physical_blocks(dfglb, 1)
    return()
    
    tmp = subset(dfglb, Max_level > 0)
    print(nrow(tmp))
    selectedfiles = sample(unique(as.character(tmp$filepath)), 100)
    plot_physical_blocks(subset(tmp, filepath %in% selectedfiles), 1)
    #plot_physical_blocks(tmp, 1)
    print("i am new")
    return ()


    samplefile = sample(tmp$filepath, 1)
    print(samplefile)
    fileext = subset(dfglb, filepath == samplefile)
    print(summary(dfglb$filepath))
    print(fileext[,2:11])
    plot_physical_blocks(fileext, 1)
}

lookat_one_file_C <- function()
{
    dfglb <<- df_filter(list.h7check01[['_extlist']], 
            p_np=8, p_nd=8, p_nf=16, p_nw=1024, 
            p_ws=256, p_wst=256, p_so=0, p_alpha=2, p_beta=5,
            p_monitor_time='year00001.season00000') 

    print(c("Max_level summary\n",summary(dfglb$Max_level)))

    #selectedfiles = sample(unique(as.character(dfglb$filepath)), 100)
    #plot_physical_blocks(subset(dfglb, filepath %in% selectedfiles), 1)
    ##plot_physical_blocks(dfglb, 1)
    #return()
    
    #tmp = subset(dfglb, Max_level > 0)
    #print(nrow(tmp))
    #selectedfiles = sample(unique(as.character(tmp$filepath)), 100)
    #plot_physical_blocks(subset(tmp, filepath %in% selectedfiles), 1)
    ##plot_physical_blocks(tmp, 1)
    #print("i am new")
    #return ()


    samplefile = sample(dfglb$filepath, 1)
    print(samplefile)
    fileext = subset(dfglb, filepath == samplefile)
    print(summary(dfglb$filepath))
    print(fileext[,2:11])
    plot_physical_blocks(fileext, 1)
}

lookat_one_file_D <- function()
{
    dfglb <<- df_filter(list.h7check01[['_extlist']], 
            p_np=8, p_nd=8, p_nf=16, p_nw=1024, 
            p_ws=256, p_wst=512, p_so=0, p_alpha=2, p_beta=5,
            p_monitor_time='year00001.season00000') 

    print(c("Max_level summary\n",summary(dfglb$Max_level)))

    #selectedfiles = sample(unique(as.character(dfglb$filepath)), 100)
    #plot_physical_blocks(subset(dfglb, filepath %in% selectedfiles), 1)
    ##plot_physical_blocks(dfglb, 1)
    #return()
    
    tmp = subset(dfglb, Max_level > 0)
    #print(nrow(tmp))
    #filepaths = unique(as.character(tmp$filepath))
    #print(c("number of files has > 0 levels:", length(filepaths)))
    #selectedfiles = sample(filepaths, 100)
    #plot_physical_blocks(subset(tmp, filepath %in% selectedfiles), 1)
    ##plot_physical_blocks(tmp, 1)
    #print("i am new")
    #return ()


    samplefile = sample(tmp$filepath, 1)
    print(samplefile)
    fileext = subset(dfglb, filepath == samplefile)
    print(summary(dfglb$filepath))
    print(fileext[,2:11])
    plot_physical_blocks(fileext, 1)
}

lookat_one_file_E <- function()
{
    monitors = levels(list.h7check01[['_extlist']]$monitor_time)
    dfglb <<- df_filter(list.h7check01[['_extlist']], 
            p_np=8, p_nd=4, p_nf=16, p_nw=4096, 
            p_ws=128, p_wst=256, p_so=0, p_alpha=5, p_beta=5,
            p_monitor_time=monitors) 

    print(c("Max_level summary\n",summary(dfglb$Max_level)))

    # look at histogram of length
    df = subset(dfglb, Level_index == Max_level)
    p <- ggplot(df, aes(x=Length, color=monitor_time))+
        geom_freqpoly(binwidth=4)+
        #geom_text(stat='bin', binwidth=1, aes(y=..count.., label=..count..), 
                    #position=position_dodge(width=50)) +
        scale_x_continuous(breaks=seq(0, 200, by=4))+
        xlab("Number of continuous blocks")+
        theme(axis.text.x=element_text(angle=45,hjust=1))+
        scale_y_log10()
    print(p)
    return(NULL)


    selectedfiles = sample(unique(as.character(dfglb$filepath)), 100)
    plot_physical_blocks(subset(dfglb, filepath %in% selectedfiles), 1)
    #plot_physical_blocks(dfglb, 1)
    return()
    
    tmp = subset(dfglb, Max_level > 0)
    #print(nrow(tmp))
    #filepaths = unique(as.character(tmp$filepath))
    #print(c("number of files has > 0 levels:", length(filepaths)))
    #selectedfiles = sample(filepaths, 100)
    #plot_physical_blocks(subset(tmp, filepath %in% selectedfiles), 1)
    ##plot_physical_blocks(tmp, 1)
    #print("i am new")
    #return ()

    samplefile = sample(tmp$filepath, 1)
    print(samplefile)
    fileext = subset(dfglb, filepath == samplefile)
    print(summary(dfglb$filepath))
    print(fileext[,2:11])
    plot_physical_blocks(fileext, 1)
}


h6ck00_main <- function()
{
    ##############################
    #############################
    #############################
    #############################
    #############################
    #############################

    #list.h6ck00 <<- files2df("C:/Users/Jun/Documents/Workdir/h6.chkpoint00")
    #save(list.h6ck00, file="list.h6ck00.no_extlist.Rdata")
    #print(str(list.h6ck00))
    
    
    #load(file="list.h6ck00._freeblocks.Rdata", globalenv())
    #df <- list.h6ck00[['_freeblocks']]
    #print(unique(list.h6ck00[['_freeblocks']]$monitor_time))
    #fdist_free_space_hist(df)

    #fdist_meta_data_blocks(list.h6ck00[['_extstatssum']])


    #############################
    #############################
    #############################
    #############################
    #############################
    #list.fdist <<- files2df("C:/Users/Jun/Documents/Workdir/h6.tar/h6")
    #save(list.fdist, file="list.fdist.Rdata")
    #print(str(list.fdist))

    #df = list.fdist[['_freeblocks']]
    #fdist_free_space_hist(df)

    #df = list.fdist[['_extstatssum']]
    ##head(df)
    #fdist_meta_data_blocks(df)
    #print(df$fs_nmetablocks)

    
    #############################
    #############################
    #############################
    #############################
    #############################
    #list.h7check00 <<- files2df("/scratch/jhe/tmp")
    #save(list.h7check00, file="list.h7check00.Rdata")
    #print(str(list.h7check00))
    

    #fdist_meta_data_blocks(list.h7check00[['_extstatssum']])
    #fdist_free_space_hist(list.h7check00[['_freeblocks']])

    #############################
    #############################
    #############################
    #############################
    #############################
    #list.h7check01 <<- files2df("/scratch/jhe/h7.check01")
    #save(list.h7check01, file="list.h7check01.Rdata")
    #load(file="list.h7check01.Rdata", globalenv())
    #print(str(list.h7check00))
    

    #fdist_meta_data_blocks(list.h7check01[['_extstatssum']])
    #fdist_free_space_hist_E(list.h7check01[['_freeblocks']])

    #lookat_one_file_A()
    #lookat_one_file_B()
    #lookat_one_file_C()
    #lookat_one_file_D()
    lookat_one_file_E()

}


