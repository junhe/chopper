load_files_by_parameters <- function(files)
{
   cclasses = c('sync'='character', 
                 'num.chunks'='numeric',
                 'chunk.order'='character',
                 'file.size'='numeric',
                 'fullness'='numeric',
                 'num.cores'='numeric',
                 'fsync'='character',
                 'num.files'='numeric',
                 'layoutnumber'='numeric',
                 'jobid'='numeric',
                 'disk.size'='numeric',
                 'file.system'='character',
                 'disk.used'='numeric',
                 'dir.span'='numeric',
                 'dspan'='numeric',
                 'layout_index'='numeric',
                 'kernel.release'='character',
                 'jobtag'='character')
    

    # input must be char
    split_column <- function(mycol, splitchar)
    {
        mycol = as.character(mycol)
        splitlist = strsplit(mycol, splitchar, fixed=T)
        df = ldply(splitlist, as.vector)
        return(df)
    }

    prepare_dataset <- function(d)
    {
        # split dspan
        df.dspan = split_column(d$datafiles_dspan, "|")
        df.dspan = as.data.frame(apply(df.dspan, 2, as.numeric))
        max.dspan = apply(df.dspan, 1, max, na.rm=T)
        n = ncol(df.dspan)
        names(df.dspan) = paste('dspan', 1:n, sep='.')
        df.dspan$max.dspan = max.dspan

        df.ext = split_column(d$num_extents, "|")
        df.ext = as.data.frame(apply(df.ext, 2, as.numeric))
        max.extcount = apply(df.ext, 1, max, na.rm=T)
        n = ncol(df.ext)
        names(df.ext) = paste('numext', 1:n, sep='.')
        df.ext$max.extcount = max.extcount

        d = cbind(d, df.dspan, df.ext)
        return(d)
    }


    d = data.frame()
    for ( file in files ) {
        print(paste('working on', file))
        path = paste('', file, sep="")
        dd = read.table(path, header=T, colClasses=cclasses)
        if ( file == 'agga.fixedimg-3.5.0.txt' ) {
            dd$jobtag = 'v1'
        }

        d = rbind(d, dd)
    }

    d$jobid = interaction(d$kernel.release, d$jobtag)

    d = prepare_dataset(d)

    return(d)
}


make_it_wide <- function(d)
{
    d = melt(d, id=c("disk.size","file.system","disk.used",
                 "layoutnumber","dir.span","sync",
                 "num.chunks","chunk.order","file.size",
                 "fullness","num.cores","fsync",
                 "num.files","jobtag"),
             measure=c("max.dspan", "max.extcount"))

    d.wide <- dcast(d, disk.size+file.system+disk.used+
                  layoutnumber+dir.span+sync+
                  num.chunks+chunk.order+file.size+
                  fullness+num.cores+fsync+
                  num.files~jobtag+variable, value.var="value")
    names(d.wide) = gsub("_max.dspan", "", names(d.wide))
    #names(d.wide) = gsub("_max.extcount", "", names(d.wide))
    return(d.wide)
}

rename_jobtag <- function(dd)
{
    dd$jobtag.old = dd$jobtag
    dd$jobtag = factor(dd$jobtag)
    remapdic =  c( 
                 'nosetaffinity'    = 'Vanilla',
                 "optspace"          ='Vanilla.optspace',
                 "optspace2"         ='vanilla2',
                 "optspace3"         ='vanilla3',
                 'inomodulo'        = '!SD',
                 'optspaceRmtail'   ='!SE',
                 'nolastbig'        ='!SG',
                 'optspacegoodnorm' ='!NB',
                 'rmtailgoodnorm'   ='!(NB | SE)',
                 'xSDxSE'           ='!(SD | SE)',
                 'xSDxSExSG'        ='!(SD | SE | SG)',
                 'nolastbiggoodnormrmtail' = '!(SG | NB | SE)',
                 'inomodNLBGNRT'    ='!(SD | SE | SG | NB)',
                 'percpu0nolastbiggoodnormrmtail' = '!(SD | SE | SG | NB) old',
                 'inomodulo2'       = '8.inum. 2',
                 'nosetaffinity1cpu'    = '1 CPU',
                 'nosetaffinity2cpu'    = '2 CPU'
                 ) 
    levels(dd$jobtag) = revalue(levels(dd$jobtag), remapdic)
    l = levels(dd$jobtag)
    extra = setdiff(l, remapdic)
    full  = c(remapdic, extra)
    dd$jobtag = factor(dd$jobtag, full)
    return(dd)
}

theme_paper <- function()
{
    return (  theme_bw() +
              theme(axis.line    =element_line(color='black')) +
              theme(panel.grid   =element_blank()) +
              theme(panel.border =element_blank()) +
              theme(legend.position='top') +
              theme(legend.title = element_blank()) +
              theme(legend.key = element_blank()) 
              #theme(plot.margin = unit(c(0,0,0,0), "cm"))
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

format_si_factor <- function(x, ...) {
    x = factor(x)
    l = as.numeric(levels(x))
    levels(x) = format_si(l, ...)
    return (x)
}


rename_factors <- function(fvec)
{
   map = c("disk.size"      ="DiskSize",
           "disk.used"      ="UsedRatio",
           "layoutnumber"   ="FreeSpaceLayout",
           "file.size"      ="FileSize",
           "num.chunks"     ="ChunkCount",
           "fullness"       ="InternalDensity",
           "chunk.order"    ="ChunkOrder",
           "fsync"          ="Fsync",
           "sync"           ="Sync",
           "num.files"      ="FileCount",
           "dir.span"       ="DirectorySpan",
           "num.cores"      ="CPUCount")

    if ( class(fvec) == 'factor' ) {
        levels(fvec) = revalue(levels(fvec),
                               map)
    } else {
        fvec = revalue(fvec, map)
    }
}

arrange.data.env <- function(files)
{

    gd <- load_files_by_parameters(files)
    gd$dspan = gd$max.dspan
    d.wide <- make_it_wide(gd)
    gd <- gd
    d.wide <- d.wide
    return (list(d.long=gd, d.wide=d.wide))
}

