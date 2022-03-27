## Performance

Based on CPU usage on Counterpoint (Intel Pentium J4125)
- Music Loop - 0.7-2.0% CPU usage 
- \+ FFmpeg decoding - 4.0-5.0% CPU usage

Why does decoding use that much in Python? Is that just to do the IO? Individual core usage isn't rising above 2.0% 
so unless the process keeps getting shifted across cores IDK

