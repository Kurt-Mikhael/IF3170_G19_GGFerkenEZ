# IF3170_G19_GGFerkenEZ

## Daftar Isi

- [Deskripsi Singkat Repository](#deskripsi-singkat-repository)
- [Penjelasan Singkat Algoritma](#penjelasan-singkat-algoritma)
- [Struktur Project](#struktur-project)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [How to Run](#how-to-run)
- [Kontributor](#kontributor)

## Deskripsi Singkat Repository

Repository ini berisi implementasi Tugas Besar 1 IF3170 Inteligensi Artifisial, yaitu pencarian konfigurasi pengisian paket ke dalam peti kemas truk menggunakan algoritma *local search*. Tujuannya adalah memaksimalkan total *value* paket yang dimuat dengan tetap memenuhi constraint: paket tidak melayang dan tidak menembus dinding peti kemas, barang pecah-belah tidak berada di bawah paket lain dan tidak menjadi penyangga, serta total berat tidak melebihi kapasitas truk.

## Penjelasan Singkat Algoritma

* **Hill-Climbing**

  * *Steepest Ascent*: membangkitkan seluruh tetangga valid lalu berpindah ke tetangga terbaik selama nilainya lebih baik dari state saat ini.
  * *Sideways Move*: kayak steepest ascent, tetapi boleh berpindah ke tetangga dengan nilai sama.
  * *Random Restart*: menjalankan steepest ascent berulang kali dari initial state acak hingga banyak restart mencapai batas maksimum, lalu mengambil hasil terbaik.
  * *Stochastic*: memilih satu tetangga acak setiap iterasi dan hanya berpindah jika tetangga tersebut lebih baik.
* **Simulated Annealing
  **Algoritma memilih satu tetangga acak setiap iterasi. Tetangga yang lebih baik selalu diterima, sedangkan tetangga yang sama atau lebih buruk diterima dengan probabilitas e^(ΔE/T). Suhu T diturunkan secara geometris hingga mencapai suhu minimum. Program juga mencatat frekuensi *stuck*, yaitu ketika selama sejumlah iterasi berturut-turut tidak ditemukan tetangga yang lebih baik.
* **Genetic Algorithm**
  Algoritma yang membentuk populasi state acak, memilih orang tua dengan *roulette wheel selection*, melakukan *crossover* per paket dan *mutation* (tukar, pindah, atau rotasi paket), lalu mengulanginya sebanyak jumlah iterasi (generasi). Eksperimen dilakukan dalam dua rangkaian: populasi sebagai kontrol dengan tiga variasi iterasi, dan iterasi sebagai kontrol dengan tiga variasi populasi.

Langkah tetangga yang digunakan adalah menukar dua paket, memindahkan sebuah paket ke koordinat lain, dan merotasi paket 90° terhadap sumbu x, y, atau z. Setiap tetangga dihasilkan dari tepat satu langkah tersebut dan hanya tetangga yang memenuhi seluruh constraint yang dipertimbangkan.

## Struktur Project

```
IF3170_G19_GGFerkenEZ
├── docs/
│   └── latex/                      # sumber dan PDF laporan
├── output/
│   └── <nama tc>/                  # hasil run algoritma (JSON) per test case
├── src/
│   ├── algorithms/
│   │   ├── common.py               # format hasil run
│   │   ├── hill_climb.py           # steepest ascent, sideways, random restart, stochastic
│   │   ├── simulated_annealing.py
│   │   └── genetic_algorithm.py
│   ├── constraints.py              # validasi constraint state
│   ├── initialization.py           # pembangkitan initial state acak
│   ├── main.py                     # program utama (CLI)
│   ├── neighbors.py                # pembangkitan tetangga (swap, move, rotate)
│   ├── objective.py                # objective function
│   ├── package.py, placement.py, problem.py, reader.py, state.py, truck.py
│   └── visualization_charts.py     # grafik hasil eksperimen
├── test/                           # test case (tc1.json - tc10.json)
├── requirements-visualization.txt
└── README.md
```

## Prerequisites

Sebelum menjalankan program, pastikan perangkat Anda telah terpasang:

* Python 3.10 atau lebih baru
* pip (hanya untuk memasang library visualisasi)

Algoritma *local search* hanya menggunakan library standar Python. Library tambahan (`plotly` dan `pandas`) hanya diperlukan untuk visualisasi.

## Setup

1. Clone repository dengan menjalankan perintah:

```bash
git clone https://github.com/Kurt-Mikhael/IF3170_G19_GGFerkenEZ.git
```

atau unduh zip proyek ini dan extract folder

2. Masuk ke direktori proyek dengan menjalankan perintah:

```bash
cd IF3170_G19_GGFerkenEZ
```

<<<<<<< HEAD
3. (Opsional, untuk visualisasi) Pasang library yang dibutuhkan:

```bash
pip install -r requirements-visualization.txt
```

=======

>>>>>>> main
>>>>>>>
>>>>>>
>>>>>
>>>>
>>>
>>

## How to Run

Jalankan program dari root repository:

```bash
python src/main.py --input <path test case> [argumen opsional]
```

Tanpa argumen tambahan, program menjalankan seluruh algoritma sesuai cakupan tugas:

* Setiap algoritma selain Genetic Algorithm dijalankan sebanyak 3 kali dengan seed berbeda.
* Genetic Algorithm dijalankan dalam dua rangkaian eksperimen (populasi sebagai kontrol dengan 3 variasi iterasi, serta iterasi sebagai kontrol dengan 3 variasi populasi), masing-masing konfigurasi sebanyak 3 kali.

Contoh:

```bash
python src/main.py --input test/tc8.json
```

Hasil setiap run disimpan dalam format JSON di `output/<nama tc>/`, berisi state awal dan akhir, nilai objective function, riwayat nilai per iterasi, durasi pencarian, serta metrik khusus setiap algoritma.

Argumen opsional:

| Argumen                      | Default        | Keterangan                                                                                                                          |
| ---------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `--algorithm`              | `all`        | `steepest_ascent`, `sideways`, `stochastic`, `random_restart`, `simulated_annealing`, `genetic_algorithm`, atau `all` |
| `--runs`                   | `3`          | banyak run per algoritma atau per konfigurasi GA                                                                                    |
| `--seed`                   | `42`         | seed run pertama; run berikutnya memakai seed + 1, seed + 2, dst.                                                                   |
| `--output-dir`             | `output`     | folder penyimpanan hasil                                                                                                            |
| `--max-sideways`           | `10`         | batas maksimum sideways move                                                                                                        |
| `--max-restart`            | `3`          | batas maksimum restart                                                                                                              |
| `--max-iterations`         | `10000`      | batas iterasi Stochastic Hill-Climbing                                                                                              |
| `--sa-initial-temperature` | `100`        | suhu awal Simulated Annealing                                                                                                       |
| `--sa-minimum-temperature` | `0.1`        | suhu minimum Simulated Annealing                                                                                                    |
| `--sa-cooling-rate`        | `0.995`      | faktor pendinginan Simulated Annealing                                                                                              |
| `--sa-max-iterations`      | `10000`      | batas iterasi Simulated Annealing                                                                                                   |
| `--sa-stuck-patience`      | `100`        | banyak iterasi berturut-turut tanpa tetangga yang lebih baik agar dianggap *stuck*                                                |
| `--ga-population-size`     | `50`         | jumlah populasi kontrol Genetic Algorithm                                                                                           |
| `--ga-iterations`          | `100`        | banyak iterasi kontrol Genetic Algorithm                                                                                            |
| `--ga-iteration-variants`  | `50 100 200` | tiga variasi banyak iterasi (populasi = kontrol)                                                                                    |
| `--ga-population-variants` | `20 50 100`  | tiga variasi jumlah populasi (iterasi = kontrol)                                                                                    |

## Kontributor

| NIM      | Nama                     | Pembagian Tugas                                                                                                                |
| :------- | :----------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| 13524062 | Nathan E C Marpaung      | 1. Penyusunan representasi problem masalah<br />2. Genetic Algorithm<br />3. Visualisasi                                       |
| 13524065 | Kurt Mikhael Pruba       | 1. Penyusunan representasi problem masalah<br />2. HC - Steepest Ascent<br />3. HC - Sideways Move<br />4. HC - Random restart |
| 13524089 | Aurelia Jennifer Gunawan | 1. Penyusunan representasi problem masalah<br />2. Simulated Annealing<br />3. HC - Stochastic                                 |
