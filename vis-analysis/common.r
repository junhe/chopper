library(RCurl)

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
                 'jobtag'='character'
                 )

    # each row in mycol is of the form '333|44'
    # This function returns the max number of each row
    get_max_element <- function(mycol)
    {
        mycol = as.character(mycol)
        elemlist = strsplit(mycol, split = '|', fixed=T)
        # convert to num
        elemlist = lapply(elemlist, as.numeric)

        maxs = lapply(elemlist, max, na.rm=TRUE)
        # convert to vector
        maxs = unlist(maxs)    
        
        return(maxs)
    }

    prepare_dataset <- function(d)
    {
        df.dspan = data.frame(max.dspan = 
                              get_max_element(d$datafiles_dspan))

        df.ext = data.frame(max.extcount = 
                            get_max_element(d$num_extents))

        d = cbind(d, df.dspan, df.ext)
        return(d)
    }

    d = data.frame()
    for ( file in files ) {
        if (exists('USE.REMOTE.CHOPPER') && USE.REMOTE.CHOPPER == TRUE) {
            path = paste('https://raw.githubusercontent.com/junhe/chopper/master/vis-analysis/', 
                         file, sep="")
            print(path)
            datatext <- getURL(path)
            dd = read.table(text=datatext, header=T, colClasses=cclasses)
        } else {
            path = file
            dd = read.table(file=path, header=T, colClasses=cclasses)
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

