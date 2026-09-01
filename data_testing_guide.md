Veri İşleme Kodu Nasıl Test Edilir? Endüstri Standartları ve İleri Düzey Doğrulama Stratejileri

Giriş: Veri Mühendisliğinde Test Etmenin Zorlukları

Yazılım mühendisliğinde geleneksel birim testleri (unit tests), belirli girdiler karşılığında kesin çıktıların üretilip üretilmediğini kontrol etmek üzerine kuruludur. Ancak söz konusu veri işleme, büyük veri setleri, ETL (Extract, Transform, Load) boru hatları (pipelines) veya log analiz sistemleri olduğunda, geleneksel birim testler yetersiz kalır. Veri mühendisliği projelerinde veriler dinamiktir, dış kaynaklardan gürültülü gelir ve hacimleri gigabaytlar veya terabaytlar mertebesindedir.

Bir veri işleme kodunu güvenilir kılmak, sadece kodun syntax veya mantık hatalarından arınmış olmasını sağlamakla kalmaz; aynı zamanda verinin kalitesini, tutarlılığını ve zaman içindeki kararlılığını garanti altına almayı gerektirir. Endüstride ve kritik mülakatlarda bir adayı öne çıkaran şey, veri işleme süreçlerini Şema Testi, Invariant Doğrulaması, Altın Dosya (Golden File) Testleri ve Property-Based Testler gibi 4 ana sütun üzerinde test edebilme yetkinliğidir.

1. Şema Testi (Schema Testing): Veri Tipinin ve Yapısının Garanti Altına Alınması
Veri işleme pipeline'larının en zayıf halkası, beklenmeyen şema değişiklikleridir. Örneğin, upstream (kaynak) sistemde bir müslümanın yanlışlıkla bir sütun adını değiştirmesi, float gelmesi gereken bir alanın string veya None (null) gelmesi, veri işleme kodunun sessizce çökmesine ya da yanlış sonuçlar üretmesine neden olur.

Şema testi, işleme giren ve çıkan veri çerçevelerinin (DataFrame) sütun adlarını, veri tiplerini, null olabilirlik kısıtlarını ve değer aralıklarını dinamik olarak denetler. Python ekosisteminde bu iş için Pandera ve Pydantic kütüphaneleri altın standarttır.

Pandera ile Şema Doğrulama Örneği

import pandas as pd
import pandera as pa
from pandera import Column, Check, DataFrameSchema

# Beklenen katı veri şemasını tanımlama
user_schema = DataFrameSchema({
    "user_id": Column(int, Check.gt(0), nullable=False),
    "age": Column(int, Check.between(0, 120), nullable=True),
    "email": Column(str, Check.str_matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")),
    "signup_date": Column(pd.DatetimeTZDtype, nullable=False)
})

def process_user_records(df: pd.DataFrame) -> pd.DataFrame:
    # Şema doğrulaması otomatik olarak çalışır ve uyumsuzlukta hata fırlatır
    validated_df = user_schema.validate(df)
    
    # İşleme mantığı
    validated_df["is_active"] = validated_df["age"] >= 18
    return validated_df

Bu yaklaşım, verinin henüz pipeline'ın başındayken filtrelenmesini sağlar ve "garbage in, garbage out" (çöp girerse çöp çıkar) kuralını erkenden engeller.

2. Invariant (Değişmezler) Testleri: Mantıksal Kuralların Korunumu
Veri dönüştürme (transformation) süreçlerinde, verinin boyutu veya biçimi değişse bile asla değişmemesi gereken matematiksel ve mantıksal kurallar vardır. Bunlara invariant adı verilir. Bir veri işleme fonksiyonu ne kadar karmaşık olursa olsun, invariant testleri kodun mantıksal bir çelişkiye düşmediğini kanıtlar.

Satır Sayısı Sınırları: Örneğin, bir filtreleme (filtering) adımından geçen veri setinin satır sayısı asla başlangıçtaki satır sayısından büyük olamaz (len(output) <= len(input)).

Toplamsal Korunum (Conservation of Mass): Finansal veya sayaç tabanlı verilerde, gruplama (groupby) işlemlerinden sonra alt toplamların ana toplama eşit olması gerekir.

Kritik Alanlarda Null Kontrolü: PRIMARY KEY veya ID niteliği taşıyan sütunlarda işlem sonrasında asla eksik (NaN) veri türememelidir.

Invariant Testi Örneği (pytest ile)

import pytest

def test_aggregation_invariants(raw_df, processed_df):
    # Invariant 1: Satır sayısı asla artmamalı (filtreleme yapıldıysa azalmalı)
    assert len(processed_df) <= len(raw_df), "Hata: Filtreleme adımında satır sayısı arttı!"
    
    # Invariant 2: Toplam ciro dönüşümden sonra korunmalı
    raw_total_revenue = raw_df["revenue"].sum()
    processed_total_revenue = processed_df["revenue"].sum()
    assert pytest.approx(raw_total_revenue, 0.01) == processed_total_revenue, "Hata: Gelir toplamında veri kaybı var!"

3. Altın Dosya (Golden File) Testleri: Büyük Çıktıların Karşılaştırılması
Karmaşık bir veri işleme fonksiyonu; yüzlerce satırlık karmaşık bir JSON, milyonlarca kayıt içeren özet CSV veya yapılandırılmış Parquet dosyaları üretebilir. Bu tarz büyük ve karmaşık çıktıların her bir satırını manuel olarak birim testlerinde assert ile kontrol etmek imkansızdır.

Altın dosya test stratejisinde, kodun kusursuz çalıştığı bilinen dönemde üretilmiş referans bir çıktısı "Altın Dosya" (golden reference file) olarak version control (git) sisteminde saklanır. Her test çalıştırıldığında, güncel kodun ürettiği çıktı bu referans dosyayla bayt bazında veya şema bütünlüğünde karşılaştırılır.

import pandas as pd
import os
import pytest

@pytest.mark.parametrize("dataset_name", ["sales_Q1", "sales_Q2"])
def test_pipeline_golden_output(dataset_name):
    input_path = f"tests/data/input_{dataset_name}.csv"
    output_df = run_heavy_etl_pipeline(input_path)
    
    golden_path = f"tests/golden/expected_{dataset_name}.parquet"
    
    if not os.path.exists(golden_path):
        # Eğer altın dosya henüz yoksa (ilk kurulum), referans olarak kaydedilir
        output_df.to_parquet(golden_path)
        pytest.skip("Altın dosya ilk kez oluşturuldu, lütfen kontrol edin.")
        
    expected_df = pd.read_parquet(golden_path)
    
    # Pandas DataFrame karşılaştırma aracı
    pd.testing.assert_frame_equal(output_df, expected_df, check_like=True)

4. Property-Based Testler (Özellik Tabanlı Testler): Uç Durumların Keşfi
Geleneksel birim testlerde geliştirici test senaryosunu kendi hayal gücüyle (örneğin: [1, 2, 3] veya [-1, 0, 5]) yazar. Ancak gerçek dünyadaki kullanıcılar ve veriler geliştiricinin akıl edemeyeceği kadar tuhaf girdiler üretebilir (aşırı büyük sayılar, özel karakterler, boş stringler, overflow durumları).

Property-based testing, fonksiyonun input değerinden bağımsız olarak her zaman sağlaması gereken genel özellikleri (properties) tanımlar. Hypothesis gibi kütüphaneler, bu kurallara uymayan binlerce rastgele ve uç (edge case) girdiyi otomatik olarak üreterek kodu çözer ve hatanın kaynağını izole eder.

Hypothesis ile Property-Based Test Örneği

from hypothesis import given, strategies as st

def custom_moving_average(data: list[float], window_size: int) -> list[float]:
    # Basit bir hareketli ortalama simülasyonu
    if not data or window_size <= 0:
        return []
    res = []
    for i in range(len(data) - window_size + 1):
        window = data[i:i+window_size]
        res.append(sum(window) / len(window))
    return res

@given(st.lists(st.floats(allow_nan=False, allow_inf=False), min_size=5, max_size=50), st.integers(min_value=1, max_value=4))
def test_moving_average_properties(data, window_size):
    result = custom_moving_average(data, window_size)
    
    # Kural 1: Çıktı uzunluğu matematiksel formüle tam uymalı
    assert len(result) == len(data) - window_size + 1
    
    # Kural 2: Çıktı elemanları asla NaN veya sonsuz olmamalı
    for val in result:
        assert isinstance(val, float)

Sonuç: Mülakat Başarısı İçin Stratejik Özet
Veri işleme kodunu test etmek, yalnızca pytest komutu çalıştırıp yeşil ışık görmek ibaret değildir. Profesyonel bir veri mühendisi veya yazılımcı; verinin yapısını Pandera ile korur, iş kurallarını invariantlar ile sınırlar, karmaşık çıktıları Golden File ile doğrular ve yazılımın dayanıksız kalabileceği uç durumları Property-Based Testing ile robottan geçirir. Bu dörtlü yaklaşım, mülakatlarda teknik olgunluğunuzu kanıtlayan en güçlü silahtır.