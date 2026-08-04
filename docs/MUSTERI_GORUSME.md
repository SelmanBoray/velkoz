# Müşteri görüşme kılavuzu

Bu, Vel'Koz'un en ucuz ve en yüksek getirili işi. **Sıfır lira tutar**, her destek başvurusunun
kalitesini ikiye katlar. TÜBİTAK BiGG ve kuluçka başvuruları "kaç potansiyel müşteriyle
konuştun?" diye sorar — "hiç" cevabı başvuruyu bitirir.

**Hedef: 5-10 görüşme.** Her biri 15-20 dakika.

---

## Kime gidilir

| Segment | Kime ulaşılır | Nasıl bulunur |
|---|---|---|
| Site/apartman yönetimi | Site yöneticisi, yönetim şirketi | Kendi sitendekiyle başla — en kolay ilk görüşme |
| AVM | Güvenlik müdürü / operasyon müdürü | Danışmadan güvenlik amirine yönlendirme iste |
| Lojistik deposu | Depo sorumlusu, güvenlik amiri | Organize sanayi bölgesi, kargo şubeleri |
| Fabrika | İş güvenliği uzmanı, güvenlik şefi | Üniversite kariyer merkezi bağlantıları |
| Kamera kurulum firması | Sahibi/teknisyeni | **En değerli segment** — yüzlerce müşterinin derdini biliyor |

> Kurulum firmalarını atlama. Bir görüşme, on son-kullanıcı görüşmesi kadar bilgi verir ve
> ileride **satış kanalın** olabilir.

---

## Altın kural

**Ürünü anlatma. Sorunu dinle.**

İlk 15 dakikada Vel'Koz'dan hiç bahsetme. Bahsedersen nezaketen "güzelmiş" derler ve öğrenecek
hiçbir şey kalmaz. Amaç onay toplamak değil, **gerçeği öğrenmek**.

---

## Sorular (sırayla)

**1. Isınma — bağlamı anla**
> "Kaç kameranız var, kayıtlar ne kadar süre saklanıyor?"

**2. Sıklık — problem gerçek mi**
> "Kayıtlara en son ne zaman geri dönmek zorunda kaldınız? Ne olmuştu?"

*Bu en önemli soru.* "Geçen hafta" derse problem canlı. "Hatırlamıyorum" derse bu segment
senin müşterin değil — bunu öğrenmek de kazançtır.

**3. Süre — acının büyüklüğü**
> "O olayda kaydı bulmanız ne kadar sürdü?"

Rakam al. "Uzun sürdü" yetmez, "yaklaşık kaç saat?" diye sor. Bu rakam pitch'ine girecek.

**4. Kim yapıyor — maliyet**
> "Bu işi kim yapıyor? Başka işi varken mi yapıyor?"

Saatlik maliyeti buradan hesaplarsın.

**5. Kaçırma — riskin bedeli**
> "Hiç aradığınızı bulamadığınız oldu mu? Sonucu ne oldu?"

**6. Mevcut çözüm — rakip gerçekte kim**
> "Şu an bu işi kolaylaştıran bir yazılımınız var mı? Kullanıyor musunuz?"

Çoğu zaman cevap: "var ama kullanmıyoruz". Nedenini sor — asıl bilgi orada.

**7. Veri hassasiyeti — KVKK argümanını test et**
> "Kamera görüntülerinizi bir bulut hizmetine yüklemek konusunda ne düşünürsünüz?"

Bu soruyu **yönlendirmeden** sor. Cevap KVKK argümanının gerçekten satın alma kararını
değiştirip değiştirmediğini gösterir. Umduğun cevabı almazsan bu değerli bir bilgidir —
konumlandırmayı değiştirirsin.

**8. Karar — kim satın alır**
> "Böyle bir şeye karar verecek kişi kim olurdu?"

**9. Bütçe — ancak buraya kadar geldiyse**
> "Bu iş için ayrılmış bir bütçe var mı, yoksa vaka bazında mı ilerliyor?"

---

## Ancak burada ürünü göster (son 5 dakika)

Demo göster, sonra tek soru:

> "Böyle bir şeyi bir hafta boyunca kendi kayıtlarınızda denemek ister miydiniz?"

**"Evet" diyen kişi pilot adayıdır — iletişim bilgisini al ve takip et.**

---

## Kaçınılacak sorular

| Sorma | Neden |
|---|---|
| "Bu ürünü sever miydiniz?" | Nezaketen evet der, bilgi sıfır |
| "Buna ayda 500 TL verir miydiniz?" | Varsayımsal fiyat sorusu, cevabı işe yaramaz |
| "Şöyle bir özellik olsa iyi olmaz mıydı?" | Kendi fikrini onaylatmış olursun |

Geçmişte **ne olduğunu** sor, gelecekte ne yapacağını değil.

---

## Kayıt şablonu

Her görüşmeden sonra hemen doldur — bir gün sonra detaylar kaybolur.

```
Tarih:
Kurum / segment:
Görüşülen kişi (rol):

Kamera sayısı:              Saklama süresi:
Son geri dönme olayı:       Ne kadar sürdü:
Bu işi kim yapıyor:
Kaçırılan olay oldu mu:
Mevcut yazılım (kullanılıyor mu):
Buluta yükleme konusundaki tepki:
Karar verici:
Bütçe durumu:

Pilot ilgisi: (evet / belki / hayır)
İletişim:

Beni en çok şaşırtan şey:
```

Son satır en değerlisidir. Varsayımının yanlış çıktığı yer, öğrendiğin yerdir.

---

## Görüşmelerden sonra

5 görüşme bitince şu üç soruyu cevapla:

1. **Ortak acı ne?** Herkesin söylediği tek cümle nedir?
2. **Hangi segment en çok acı çekiyor?** İlk müşterin oradan çıkar.
3. **Hangi varsayımın yanlış çıktı?** (Örn. KVKK kimsenin umurunda değilse konumlandırmayı
   değiştir.)

Bu üç cevap doğrudan `ONE_PAGER.md` ve `PITCH_DECK.md` 3. slayta yazılır.
