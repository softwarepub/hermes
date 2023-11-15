from pydalos.linked_data import LDTerm


def test_ldterm_equal():
    assert LDTerm('https://schema.org/Thing') == LDTerm('https://schema.org/Thing')
    assert LDTerm('https://schema.org/Thing') == 'https://schema.org/Thing'
    assert 'https://schema.org/Thing' == LDTerm('https://schema.org/Thing')


def test_ldterm_not_equal():
    assert LDTerm('https://schema.org/Thing') != LDTerm('https://schema.org/Taxon')
    assert LDTerm('https://schema.org/Thing') != 'https://schema.org/Taxon'
    assert 'https://schema.org/Thing' != LDTerm('https://schema.org/Taxon')


def test_ldterm_dict_key():
    data = {
        LDTerm('https://schema.org/Thing'): 'spam'
    }

    assert 'spam' == data[LDTerm('https://schema.org/Thing')]
    assert 'spam' == data['https://schema.org/Thing']
