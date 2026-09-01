# Kontrol Soruları ve Teknik Çözümler

Bu dosyada, veri odaklı Python programlama sürecinde mülakatlarda ve ileri düzey mühendislik görevlerinde karşılaşılan kritik kontrol soruları ve detaylı teknik gerekçelendirmeleri yer almaktadır.

---

## 1. `list` Yerine `deque` Kullanılması Gereken Senaryo ve Big-O Gerekçesi

### Senaryo
Yüksek trafikli bir web sunucusunda anlık gelen log kayıtlarını veya chat mesajlarını sırasıyla işleyen bir kuyruk (**FIFO - First In First Out**) sistemi tasarlıyorsun. Gelen veriler sürekli kuyruğun sonuna eklenir (`append`), en eski veriler ise kuyruğun başından işlenip çıkarılır (`pop`).

### Big-O Gerekçesi
* **`list`:** Python'daki standart `list` veri yapısı arkasında dinamik bir dizi (`array`) barındırır. Listeye `pop(0)` veya `insert(0, item)` ile en baştan bir eleman silmek ya da eklemek, arkadaki tüm elemanların bellekte birer adım kaydırılmasını gerektirir. Bu durum **$O(N)$** zaman karmaşıklığına yol açar. Milyonlarca elemanlı bir listede başa eleman eklemek/çıkarmak sistemi ciddi oranda yavaşlatır.
* **`deque` (`collections.deque`):** Çift yönlü bağlı liste (`doubly linked list`) mimarisiyle çalışır. Hem sağdan hem soldan $O(1)$ sabit zaman karmaşıklığıyla eleman ekleme ve çıkarma (`appendleft`, `popleft`) yapabildiği için kuyruk mimarilerinde kesinlikle `deque` tercih edilmelidir.

---

## 2. Bir Decorator'da `functools.wraps` Kullanmazsam Ne Kaybederim?

Bir decorator yazdığında, ana fonksiyonu sarmalayıp (`wrapper`) geri döndürürsün. Eğer `functools.wraps(func)` kullanmazsan şu kritik metaları ve özellikleri kaybedersin:
1. **Metadata Kaybı:** Fonksiyonun orijinal adı (`__name__`), docstring'i (`__doc__`) ve modül bilgisi kaybolur; bunun yerine wrapper fonksiyonun bilgileri görünür.
2. **Dokümantasyon ve Introspection Bozulması:** `help(fonksiyon_adi)` veya IDE ipuçları (`docstrings`) fonksiyonun orijinal açıklamalarını gösteremez.
3. **Test Çerçeveleri (`pytest` vb.):** Pytest veya mock kütüphaneleri, fonksiyonları `__name__` üzerinden tanıdığı için testler yanlış çalışabilir veya loglama mekanizmaları izlenebilirliğini yitirir. `wraps`, orijinal fonksiyonun tüm özniteliklerini sarmalayıcıya güvenle kopyalar.

---

## 3. `Protocol` ile `ABC` (Abstract Base Classes) Arasındaki Fark

* **ABC (Nominal Subtyping):** Kalıtım odaklıdır. Bir sınıfın belirli bir arayüzü sağlaması için o soyut sınıfı açıkça miras alması (`class MyClass(MyABC):`) şarttır. Sınıflar arasında sıkı bir hiyerarşi (`isinstance` kontrolleri vb.) kurulur.
* **Protocol (Structural Subtyping / Duck Typing):** Şekilsel/yapısal uyumluluğa dayanır. Sınıfın herhangi bir atadan türemesine gerek yoktur; sadece Protocol'ün tanımladığı metot imzalarına (`def method():`) sahip olması yeterlidir. 

**Örnek Senaryo:** Harici bir kütüphaneden gelen ve üzerinde değişiklik yapamadığın bir sınıf, senin arayüz özelliklerini taşıyorsa `Protocol` ile hiçbir `inherit` (kalıtım) yapmadan doğrudan kullanılabilirken, `ABC` ile bu imkansızdır.

---

## 4. 100 GB'lık CSV Dosyasını 8 GB RAM'de İşleme Stratejileri

8 GB RAM'e sahip bir makinede 100 GB'lık devasa bir CSV dosyasını tek seferde `pd.read_csv()` ile okumak `MemoryError` ile sistemi çökertecektir. Bunu çözmek için 3 farklı endüstriyel strateji vardır:

1. **Chunking (Parça Parça Okuma):** Pandas'ın `chunksize` parametresi kullanılarak dosya örneğin 100.000 satırlık küçük parçalar halinde döngüyle okunur ve işlenir.
2. **Lazy Evaluation / PyPolars veya DuckDB:** Veriyi belleğe yüklemek yerine sütun tabanlı ve optimize edilmiş `Polars` kütüphanesi veya `DuckDB` kullanılarak sorgular disk üzerinden tembel (lazy) bir şekilde yürütülür.
3. **Dask / PySpark Kullanımı:** Veri kümesi cluster mimarisine veya paralel chunk mekanizmasına bölünerek paralelleştirilmiş disk/bellek yönetimiyle işlenir.

---

## 5. `pytest` Fixture'ının `scope` Parametresi ve Veritabanı Testleri

`pytest` fixture'larının `scope` parametresi, bir test kaynağının (örneğin veritabanı bağlantısı veya test verisi) ne sıklıkla oluşturulup yok edileceğini belirler:
* `scope="function"` (Varsayılan): Her bir test fonksiyonu için ayrı çalışır.
* `scope="module"`: Python dosyası başına bir kez çalışır.
* `scope="session"`: Tüm test oturumu boyunca bir kez çalışır.

**Veritabanı Testinde Hangisi Seçilir?:**
* Eğer testler veritabanını değiştirmiyorsa ve sadece okuma yapıyorsa hız kazandırmak için **`scope="session"`** veya **`scope="module"`** tercih edilebilir.
* Ancak veritabanı testi yazarken her testin izole (temiz bir state ile) başlaması gerektiğinden, testler veriyi kirletiyorsa (insert/update/delete) her test fonksiyonu için sıfırdan veritabanı ayağa kaldıran **`scope="function"`** veya her test başında işlem roll-back yapan fixture yapıları seçilmelidir. 