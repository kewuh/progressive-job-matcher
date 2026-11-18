#!/usr/bin/env python3
"""Print the Job Scout document id for a job: job_id.py <url> <title>.

Same as the dashboard's JavaScript:
  function hash(s){let h=5381;for(const c of s)h=((h<<5)+h+c.charCodeAt(0))>>>0;return "j"+h.toString(36);}
applied to url + "|" + title.toLowerCase().
"""
import sys


def job_id(url, title):
    h = 5381
    for ch in url + "|" + title.lower():
        h = ((h << 5) + h + ord(ch)) & 0xFFFFFFFF
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    s = ""
    while h:
        s = digits[h % 36] + s
        h //= 36
    return "j" + (s or "0")


if __name__ == "__main__":
    print(job_id(sys.argv[1], sys.argv[2]))
