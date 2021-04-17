fName = commandArgs(trailingOnly = T)[1]
if (is.na(fName)) {
  # stop('no video file name provided')
  fName = 'videotrim.mp4'
}

timeToSecs = function(x) {
  sum(as.double(strsplit(x, ':')[[1]])  * c(3600, 60, 1))
}

silenceCmd = paste('ffmpeg -hide_banner -nostats -i', fName, '-af silencedetect=noise=-30dB:d=15 -f null - 2>&1')
iframeCmd = paste('ffprobe -select_streams v -skip_frame nokey -show_frames -show_entries frame=pkt_pts_time,pict_type', fName)

rawFrames = system(iframeCmd, intern = T)
ptsLines = rawFrames[grepl('pkt_pts_time', rawFrames, fixed=T)]
frames = as.double(regmatches(ptsLines, regexpr('\\d+\\.\\d+', ptsLines)))

rawOutput= system(silenceCmd, intern = T)
silenceStarts = rawOutput[grepl("silence_start", rawOutput, fixed=T)]
silenceEnds = rawOutput[grepl("silence_end", rawOutput, fixed=T)]
durationStr = rawOutput[grepl("Duration:", rawOutput, fixed=T)]
duration = timeToSecs(regmatches(durationStr, regexpr("\\d\\d:\\d\\d:\\d\\d\\.\\d\\d", durationStr)))

intEnds= c(as.double(unlist(lapply(strsplit(silenceStarts, ' '), function(x) x[5]))), duration)
intStarts = c(0, frames[findInterval(as.double(unlist(lapply(strsplit(silenceEnds, ' '), function(x) x[5]))), frames)] - 0.1)

file.create('.tmpnames.txt')
for(i in seq(1, length(intEnds))) {
  outputName = paste("part", i, ".mp4", sep='')
  write(paste('file', outputName), '.tmpnames.txt', append=T)
  cmd = paste("ffmpeg -y -i ", fName, ifelse(i == 1, "", paste(" -ss ", intStarts[i], sep = '')), " -to ", intEnds[i], " -c copy ", outputName, sep='')
  system(cmd)
}
if (length(intEnds) > 1) {
  system('ffmpeg -y -f concat -i .tmpnames.txt -c copy nobreaks.mp4')
}
for(i in seq(1, length(intEnds))) {
  outputName = paste("part", i, ".mp4", sep='')
  file.remove(outputName)
}
file.remove('.tmpnames.txt')
