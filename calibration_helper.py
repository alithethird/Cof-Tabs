from hx711 import HX711

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.reset()
hx.tare()
count = 0

print("Az önce tare yaptı!")

print("---------------------------------------------")
print("Bilinen ağırlık miktarları girildiği an ölçüm yapıyor!")
print("---------------------------------------------")
print("modlar: 1- tek ağırlık ile kalibrasyon sayısı bulma")
print("2- 2 ağırlık ile kalibrasyon sayısı bulma")

count = input("Mod seç Umut beybisi: ")

if count == "1":
    bilinen_agirlik = input("Koyduğun ağırlık: ")
    olculen_agirlik = hx.get_weight(5)
    print("Ölçülen ağıklık: " + str(olculen_agirlik))
    print("-----------------------------------------")
    kalibrasyon_sayisi = float(bilinen_agirlik) / olculen_agirlik
    print("Kalibrasyon sayısı: " + str(kalibrasyon_sayisi))
    a = kalibrasyon_sayisi
    b = 0
elif count == "2":
    ilk_bilinen = input("İlk ağırlığın değeri: ")
    ilk_olculen = hx.get_weight(5)
    ikinci_bilinen = input("İkinci ağırlığın değeri: ")
    ikinci_olculen = hx.get_weight(5)
    # y = a*x + b
    if ikinci_olculen > ilk_olculen:
        a = (float(ikinci_bilinen) - float(ilk_bilinen)) / (ikinci_olculen - ilk_olculen)
    else:
        a = (float(ilk_bilinen) - float(ikinci_bilinen)) / (ilk_olculen - ikinci_olculen)

    b = (float(ikinci_bilinen) - (ikinci_olculen * a)) + (float(ilk_bilinen) - (ilk_olculen * a))
    b = b/2

    print("gerçek değer = a*(ölçülen değer) + b")
    print("gerçek değer = " + str(a) + "*(ölçülen değer) + " + str(b))

test = input("Kalibrasonu test etmek istersen 1'e bas")

if test == "1":
    bilinen_test = print("Koyduğun ağırlık: ")
    olculen_test = hx.get_weight(5)
    print("Ölçülen: " + str(olculen_test))
    kalibre_edilmis = a*olculen_test + b
    print("Kalibre edilmiş sonuç: " + str(kalibre_edilmis))
else:
    pass