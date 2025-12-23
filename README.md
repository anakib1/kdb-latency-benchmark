## Design

![design](static/imgs/kdb-design.svg)

Amazon setup details:

- c5d.4xlarge
- 16 vCpus
- 32 GB RAM
- Ember ansible configurations (https://github.com/epam/ember-ami-builder) run on setup.

**KDB-X preview uses at most 16 Gb memory because of imposed limitations**

## Instruction

### Prerequisites
- Python 3.9 for charts (`python` alias)
    - Run `python -m venv venv` inside py-src directory
- KDB-X installed (`q` alias)

Experiments are controlled by `THROUGHPUT` and `DURATION` env variables.

### Suite
- run `suite.sh`

### Semi-Manual
- run `run.sh`

### Manual
- `cd q-src`
- Adjust `common.q`
- Run `q tick.q trades [logs] -t 0` (`logs` makes sure it keeps WAL)
- Run `q logger.q -p 5001`
- Run `q sub.q`
- Run `q latency.q`
- Wait for completion. Results will be visible in `logger`'s process as well as `results'.txt` file. All latencies for individual requests will be stored in `times.csv` file.
- Optional:
    - `cd py-src`
    - run `draw.py`
    - It will produce `results` folder with histograms of experiment based on `times.csv` file

## Results

All latency values are reported in microseconds.

Default settings are:
- No WAL
- Unix sockets enabled
- No affinity for processes

| Throughput | 50%      | 90%      | 99%      | 99.9     | 99.99%   |
|------------|----------|----------|----------|----------|----------|
| 20000      | 34       | 36       | 40       | 44       | 53       |
| 40000      | 34       | 35       | 39       | 42       | 46       |
| 60000      | 27       | 32       | 35       | 40       | 109      |
| 80000      | 27       | 33       | 35       | 43       | 9390     |
| 120000     | overflow | overflow | overflow | overflow | overflow |

## Detailed results


**100 req/s**

![timeline](imgs/aws_100_tl.png)
![hist](imgs/aws_100_hist.png)

**10K req/s**

![timeline](imgs/aws_10K_tl.png)
![hist](imgs/aws_10K_hist.png)

**20K req/s**

![timeline](imgs/aws_20K_tl.png)
![hist](imgs/aws_20K_hist.png)