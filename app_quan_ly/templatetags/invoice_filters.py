from django import template

register = template.Library()

@register.filter
def number_to_words(value):
    """Chuyển số tiền thành chữ tiếng Việt"""
    try:
        num = int(float(value))
    except:
        return ""
    
    if num == 0:
        return "Không đồng"
    
    # Đơn vị
    ones = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    
    def read_block(n):
        """Đọc khối 3 chữ số"""
        hundred = n // 100
        ten = (n % 100) // 10
        one = n % 10
        
        result = []
        
        if hundred > 0:
            result.append(ones[hundred] + " trăm")
        
        if ten > 1:
            result.append(["", "", "hai mươi", "ba mươi", "bốn mươi", "năm mươi", 
                          "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"][ten])
            if one == 1:
                result.append("mốt")
            elif one == 5 and ten > 0:
                result.append("lăm")
            elif one > 0:
                result.append(ones[one])
        elif ten == 1:
            result.append("mười")
            if one == 5:
                result.append("lăm")
            elif one > 0:
                result.append(ones[one])
        else:
            if one > 0:
                if hundred > 0:
                    result.append("lẻ")
                result.append(ones[one])
        
        return " ".join(result)
    
    # Tách các khối tỷ, triệu, nghìn
    billion = num // 1000000000
    million = (num % 1000000000) // 1000000
    thousand = (num % 1000000) // 1000
    unit = num % 1000
    
    result = []
    
    if billion > 0:
        result.append(read_block(billion) + " tỷ")
    if million > 0:
        result.append(read_block(million) + " triệu")
    if thousand > 0:
        result.append(read_block(thousand) + " nghìn")
    if unit > 0:
        result.append(read_block(unit))
    
    words = " ".join(result).strip()
    return words.capitalize() + " đồng"