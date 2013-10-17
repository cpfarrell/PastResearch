# demographics.py
# Written by:  Alejandro Cantarero
#              alejandro.cantarero@attensitymedia.com
#
# Collection of routines to compute demographic information
#

import sys


"""   ----------------
-
-
-    Approaches to learning gender information
-
-
--------------------  """


"""     ---

   names

---     """    


# num_names:  number of top female and male names to return
def find_top_names(num_names=100):

    # process male
    f = open('data/dist.male.first', 'r')
    
    names = f.readlines()
    male_names = [items.split()[0] for items in names]

    f.close()

    # process female
    f = open('data/dist.female.first', 'r')
    
    names = f.readlines()
    female_names = [items.split()[0] for items in names]

    f.close()    

    if num_names > len(male_names):
        final_male_list = male_names
    else:
        final_male_list = male_names[:num_names]

    if num_names > len(female_names):
        final_female_list = female_names
    else:
        final_female_list = female_names[:num_names]

    return (final_male_list, final_female_list)


# find items that appear in both list1 and list2
def find_repeats(list1, list2):

    set1 = set(list1)
    return set1.intersection(list2)


"""

routines to find the top x male or female names that are not
contained in the list of the opposite gender

"""

# gender:      is string of gender names we are searching:  'male' or 'female'
# full_list:   is the full list of names of the opposite gender
# length:      number of unique names we want to find
def find_name_length_upper_bound(length, full_list, gender):

    # start with final list length we want to achieve
    length_guess = length
    (male_short, female_short) = find_top_names(num_names=length_guess)
    
    if gender == 'male':
        short_list = male_short
    else:
        short_list = female_short

    repeats = find_repeats(short_list, full_list)
    while length_guess - len(repeats) < length:
        
        # increase linearly rather than exponentially since total list lengths are so short
        length_guess = length_guess + 50
        
        (male_short, female_short) = find_top_names(num_names=length_guess)
    
        if gender == 'male':
            short_list = male_short
        else:
            short_list = female_short
        
        repeats = find_repeats(short_list, full_list)

    return length_guess


# binary search to find correct list necessary to return length unique names
# ub:  upper bound on list length
# full_list:  full list of opposite gender to compare against
# gender:  'male' or 'female'
def find_required_list(length, ub, full_list, gender):

    lb = length

    mid_pt = lb + int((ub - lb) / 2)
    (male, female) = find_top_names(mid_pt)

    if gender == 'male':
        short_list = male
    else:
        short_list = female

    repeats = find_repeats(short_list, full_list)
    list_length = len(short_list) - len(repeats)
    while list_length != length:

        # continue search
        if ub - lb == 1:
            break
        elif list_length < length:
            lb = mid_pt
        else:
            ub = mid_pt

        mid_pt = lb + int((ub - lb) / 2)
        (male, female) = find_top_names(mid_pt)

        if gender == 'male':
            short_list = male
        else:
            short_list = female

        repeats = find_repeats(short_list, full_list)
        list_length = len(short_list) - len(repeats)

    return short_list


# length of unique name lists
def find_top_non_repeated_names(length=200):

    if length > 600:
        print 'Insufficient unique names in data.  Cannot satisfy request. Reduce length to < 600.'
        sys.exit(1)

    (male_full, female_full) = find_top_names(10000)

    length_guess = length
    (male_short, female_short) = find_top_names(num_names=length_guess)

    # find male non-repeats
    ub = find_name_length_upper_bound(length, female_full, 'male')
    male_names = find_required_list(length, ub, female_full, 'male')
    male_names = [name for name in male_names if name not in female_full]

    # find female non-repeats
    ub = find_name_length_upper_bound(length, male_full, 'female')
    female_names = find_required_list(length, ub, male_full, 'female')
    female_names = [name for name in female_names if name not in male_full]

    return (male_names, female_names)
