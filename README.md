# IF3170_G19_GGFerkenEZ


## Daftar Isi
- [Deskripsi Singkat Repository](#deskripsi-singkat-repository)
- [Penjelasan Singkat Algoritma](#penjelasan-singkat-algoritma)
- [Struktur Project](#struktur-project)
- [Prerequisites](#prerequisites)
- [How to Run](#how-to-run)
- [Kontributor](#kontributor)

## Deskripsi Singkat Repository

## Penjelasan Singkat Algoritma

* **Hill-Climbing**

* **Simulated Annealing**


* **Genetic Algorithm**


## Struktur Project
```
IF3170_G19_GGFerkenEZ
├── docs/                                          
├── output/                    
├── src/ 
│   ├──       
│   │   ├──
│   │   └── 
│   ├──                
│   │   ├──   
│   │   └── 
│   └──               
│       ├──             
│       └── 
├──                           
└──        
```

## Prerequisites
Sebelum menjalankan program, pastikan perangkat Anda telah terpasang:
*   


## Setup
1. Clone repository dengan menjalankan perintah:
```bash
git clone 
```
atau unduh zip proyek ini dan extract folder

2. Masuk ke direktori proyek dengan menjalankan perintah:
```bash
cd 
```


## How to Run
1. 

## Visualisasi

Pasang dependensi visualisasi:

```bash
python -m pip install -r requirements-visualization.txt
```

Setelah hasil pencarian tersedia sebagai JSON di folder `output`, jalankan dari root repository:

```bash
python -m src.visualize --input test/tc1.json --results output
```

Buka `output/visualizations/index.html` di browser. Laporan berisi initial/final state 3D, paket di luar peti, tabel semua paket, peta sel dengan slider ketinggian `z`, grafik algoritma, dan ringkasan eksperimen. Laporan dapat dibuka tanpa internet; sertakan `plotly.min.js` ketika menyalin folder laporan.

`--input` harus menunjuk permasalahan yang digunakan untuk menghasilkan seluruh JSON tersebut. `--results` juga dapat menunjuk satu file JSON; `--output-dir` mengganti lokasi laporan. Visualisasi hanya membaca hasil dan tidak menjalankan pencarian.

Posisi paket di luar peti merupakan ilustrasi; posisi pada state tetap `None`. Nilai state adalah jumlah nilai paket di dalam. Random Restart menampilkan initial state pencarian pertama dan final state terbaik, sedangkan SA menampilkan final state terbaik sepanjang pencarian. Grafik GA mendukung format hasilnya, tetapi kode GA saat ini masih memerlukan penyelarasan API sebelum dapat menghasilkan hasil tersebut.

## Kontributor
| NIM      | Nama                           |
|:---------|:-------------------------------|
| 13524062 | Nathan E C Marpaung            | 
| 13524065 | Kurt Mikhael Pruba             |
| 13524089 | Aurelia Jennifer Gunawan       |


