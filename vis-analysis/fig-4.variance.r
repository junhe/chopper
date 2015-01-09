library(ggplot2)


primer_sa <- function(d)
{
    make_sa_formula <- function(f)
    {
        factors = paste(f, collapse="+")
        fmstr = paste('dspan~', factors, sep="")
        print(fmstr)
        fm = as.formula(fmstr)
        return(fm)
    }

    get_sen_nway <- function(d, nams) 
    {
        df.sen = NULL
        nways = length(nams[[1]])
        for ( f in nams ) {
            #print(f)
            fm = make_sa_formula(f)
            dd = aggregate(fm, data=d, mean)
            #print(dd)
            grand.mean = mean(dd$dspan)
            si = mean( (dd$dspan - grand.mean)^2 )
            #print(d)
            #print(si)
            row = c(f, si)
            df.sen = rbind(df.sen, row) 
        }
        df.sen = data.frame(df.sen)
        fnames = paste('f', seq(nways), sep="")
        sename = "sensitivity"
        nams = c(fnames, sename)
        names(df.sen) = nams
        df.sen$sensitivity = as.numeric(as.character(df.sen$sensitivity))
        return(df.sen)
    }
    
    # it returns a list containing vectors,
    # each item is one that we want to know the level mean
    get_set <- function(nways) 
    {
        #nams = c("disk.size", "sync","chunk.order", "file.size",
                 #"num.cores", "fsync", "num.files", "layoutnumber",
                 #"disk.used", "dir.span")

        nams = c("disk.size", "sync","chunk.order", "file.size", "fullness",
                 "num.cores", "fsync", "num.files", "layoutnumber",
                 "disk.used", "dir.span")
        
        a = combn(nams, nways)
        #print(a)
        a = alply(a, 2)
        print(a)
        return(a)
    }

    interaction_to_columns <- function(s)
    {
      s = as.character(s)
      n = length(unlist(strsplit(s[1], ":", fixed=T)))
      b = unlist(strsplit(s, ":", fixed=T))
      b = matrix(b, ncol=n, byrow=T)
      b = as.data.frame(b)
      suf = as.character(seq(n))
      names(b) = paste('f', suf, sep="")
      return (b)
    }

    combine_all_ways <- function(sen1way, sen2way) 
    {
      s.comb = merge(sen2way, sen1way, by.x='f1', by.y="f1", suffixes=c('', '.f1'))
      s.comb = merge(s.comb, sen1way, by.x='f2', by.y="f1", suffixes=c("", ".f2"))
      return(s.comb)
    }

    get_total_effect <- function(sen1way, sen.all)
    {
        nams = get_set(1) 

        df.ret = NULL
        for ( f in nams ) {
            d.sub = subset(sen1way, f1==f)
            #print(d.sub)
            total = d.sub$sensitivity
            d.sub = subset(sen.all, f1==f | f2==f)
            total = total + sum(d.sub$sensitivity)
            df.ret = rbind(df.ret, 
                           data.frame('f1'=f,
                                      'sensitivity'=total))
            #print(d.sub)
        }
        #print(df.ret)
        #plot_sensitivity(df.ret)
        return(df.ret)
    }

    nams = get_set(1) 
    sen1way <<- get_sen_nway(d, nams)
    nams = get_set(2) 
    sen2way <<- get_sen_nway(d, nams)

    sen.all = combine_all_ways(sen1way, sen2way)
    sen.all$inter.sen = sen.all$sensitivity - 
                        sen.all$sensitivity.f1 - 
                        sen.all$sensitivity.f2

    sen.all <<- sen.all

    sen.total <<- get_total_effect(sen1way, sen.all)

    retlist = list("way1"=sen1way, 
                   "way2"=sen2way,
                   "inter"=sen.all,
                   "total"=sen.total)

    return(retlist)
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

paper_sensitivity_plot <- function()
{

    plot_sensitivity_index <- function(d)
    {
        # sort factors by sensitivity
        d = arrange(d, sensitivity)
        print(d)
        # normalize to sensitivity index
        totalvariance = sum(d$sensitivity)
        d$sensitivity = d$sensitivity / totalvariance
        print(d)

        forder = as.character(d$f1)
        d$f1 = factor(d$f1, levels=forder)
        levels(d$f1) = rename_factors(levels(d$f1))

        p <- ggplot(d, aes(
                           x=f1,
                           y=sensitivity
                           )) +
             geom_bar(stat='identity', fill='black') +
             theme_paper() +
             coord_flip() +
             xlab("") +
             ylab("Variance Contribution") 
        print(p)
        return(p)
    }

    gd = load_files_by_parameters(files=c(
                                    "./data/agga.fixedimg-3.12.5.txt-nosetaffinity"
                                           ))
    gd$dspan = gd$max.dspan
    senlist = primer_sa(gd)
    p1 = plot_sensitivity_index(senlist[['way1']])
    #save_plot(p1, 'main-effect', w=5, h=2.5)
}

main <- function()
{
    paper_sensitivity_plot()
}

main()


