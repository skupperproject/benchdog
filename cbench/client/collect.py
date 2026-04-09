#! /usr/bin/python

#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import sys as _sys

durations = []
last_time = 0.0

print_header = _sys.argv[1]
n_clients = _sys.argv[2]

for file_name in _sys.argv[3:] :
    with open(file_name) as f:
      lines = f.readlines()
      for line in lines : 
          # format:   request_time,connection_complete_time
          # example:  0.027601,0.000699
          words = line.strip().split(',')
          if len(words) < 2 :
              continue
          # The file line are in chron order, so this will 
          # always have the last-recorded time in it.
          last_time = words[0]
          duration  = words[1]
          durations.append ( float(duration) )


sorted_durations = sorted(durations, key = lambda x:float(x))
duration_sum     = sum(sorted_durations)
average_dur      = duration_sum / len(durations)

pos_50 = int(len(durations) / 2)
pos_99 = int(len(durations) * 0.99)
dur_50 = sorted_durations[pos_50]
dur_99 = sorted_durations[pos_99]

# Convert to msec
dur_50      *= 1000
dur_99      *= 1000
average_dur *= 1000

cnx_per_sec = len(durations) / float(last_time)
cps         = f"{cnx_per_sec:.2f}  cnx/s"
avg         = f"{average_dur:.2f} ms"
d_50        = f"{dur_50:.2f} ms"
d_99        = f"{dur_99:.2f} ms"

col_1 = "CLIENTS"
col_2 = "THROUGHPUT" 
col_3 = "LATENCY AVG"
col_4 = "LATENCY P50"
col_5 = "LATENCY P99"

if print_header == "print_header" :
    print ( f"{col_1:>11}{col_2:>22}{col_3:>20}{col_4:>20}{col_5:>20}" )
print ( f"{n_clients:>11}{cps:>22}{avg:>20}{d_50:>20}{d_99:>20}" )



