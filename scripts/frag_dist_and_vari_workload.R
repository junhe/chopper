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
    source("C:/Users/Jun/Dropbox/0-Research/0-metadata/src/metawalker/scripts/frag_dist_and_vari_workload.R")
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
    #list.h7check00 <<- files2df("C:/Users/Jun/Documents/Workdir/h7.check00")
    #save(list.h7check00, file="list.h7check00.Rdata")
    #print(str(list.h7check00))
    

    #fdist_meta_data_blocks(list.h7check00[['_extstatssum']])
    fdist_free_space_hist(list.h7check00[['_freeblocks']])

}

