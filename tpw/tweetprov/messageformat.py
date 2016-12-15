from .persistent import HistoryManager
from .util import RULE_NO_1, RULE_TOP_3, RULE_BOTTOM_3, RULE_NO_PROV_SCORE


class FormattingError(Exception):
    pass

def formatNo1(db, tweet, override=False):
    for company in db.companies[tweet.community.schema]:
        if company.category is None: # discard companies without category
            continue

        if company.invalidScore or company.twitterAccount == '': # discard client with no proven score
            continue

        if not override:
            history = HistoryManager.getHistoryFor(company.id, tweet.id)

        if company.ranking == 1: # current ranking is #1, check if it's different than before
            if override or (history is None or history.category_id != company.categoryId or history.ranking != 1): # means company just ranked #1
                # report ranking to twitter
                yield tweet.message.format(**{
                    'companyname': company.twitter,
                    'categoryname': company.category,
                    'profileurl': company.url,
                    'location': company.location,
                    'score': round(company.provenScore),
                    'categoryurl': company.categoryUrl,
                    'domain': tweet.community.name,
                    'domainurl': db.domainUrl(tweet.community.schema),
                    })

                if not override:
                    # save data for later
                    HistoryManager.saveHistoryFor(company.id, company.ranking, company.categoryId, tweet)

def formatTop3(db, tweet, override=False):
    podium = {}

    # extract the valid top 3 for each category
    for company in db.companies[tweet.community.schema]:
        if company.category is None: # discard companies without category
            continue

        if company.invalidScore or company.twitterAccount == '':
            continue

        if company.ranking <= 3:
            if company.category in podium:
                podium[company.category].append(company)
            else:
                podium[company.category] = [company]

    # filter
    for category in podium.keys():
        winners = [co for co in podium[category] if not co.invalidScore]

        if len(winners) == 0:
            continue

        winners.sort(key=lambda co: co.ranking)

        params = {
            'categoryname': category,
            'categoryurl': winners[0].categoryUrl,
            'nrofcompanies': len(winners),
            'companies': ', '.join(co.twitter for co in winners),
            'domain': tweet.community.name,
            'domainurl': db.domainUrl(tweet.community.schema),
        }

        for index, winner in enumerate(winners):
            strIndex = str(index + 1) # count from 1

            params['companyname' + strIndex] = winner.twitter
            params['profileurl' + strIndex] = winner.url
            params['location' + strIndex] = winner.location
            params['score' + strIndex] = round(winner.provenScore)

        for i in range(index + 1, 3): # 3 companies max
            strIndex = str(i + 1) # count from 1

            params['companyname' + strIndex] = ''
            params['profileurl' + strIndex] = ''
            params['location' + strIndex] = ''
            params['score' + strIndex] = ''

        yield tweet.message.format(**params)

def formatBottom3(db, tweet, override=False):
    podium = {}
    
    # extract the valid top 3 for each category
    for company in db.companies[tweet.community.schema]:
        if company.category is None: # discard companies without category
            continue

        if company.invalidScore or company.twitterAccount == '':
            continue

        if company.category in podium:
            podium[company.category].append(company)
        else:
            podium[company.category] = [company]
                
    # filter
    for category in podium.keys():
        companies = sorted(podium[category], key=lambda co: co.provenScore)[-3:]

        if len(companies) == 0:
            continue

        params = {
            'categoryname': category,
            'categoryurl': companies[0].categoryUrl,
            'nrofcompanies': len(companies),
            'companies': ', '.join(co.twitter for co in companies),
            'domain': tweet.community.name,
            'domainurl': db.domainUrl(tweet.community.schema),
        }

        for index, company in enumerate(companies):
            strIndex = str(index + 1) # count from 1

            params['companyname' + strIndex] = company.twitter
            params['profileurl' + strIndex] = company.url
            params['location' + strIndex] = company.location
            params['score' + strIndex] = round(company.provenScore)

        yield tweet.message.format(**params)

def formatNoScore(db, tweet, override=False):
    for company in db.companies[tweet.community.schema]:
        if not company.invalidScore or company.twitterAccount == '': # discard client with proven score, only without are required
            continue

        yield tweet.message.format(**{
            'companyname': company.twitter,
            'categoryname': company.category if company.category is not None else 'without category',
            'profileurl': company.url,
            'location': company.location,
            'score': round(company.provenScore) if company.provenScore else 0,
            'categoryurl': company.categoryUrl if company.categoryUrl is not None else '',
            'domain': tweet.community.name,
            'domainurl': db.domainUrl(tweet.community.schema),
        })

def formatMessage(db, tweet, override=False):
    callbacks = {
        RULE_NO_1: formatNo1,
        RULE_TOP_3: formatTop3,
        RULE_BOTTOM_3: formatBottom3,
        RULE_NO_PROV_SCORE: formatNoScore,
    }

    try:
        for val in callbacks[tweet.rule.rule](db, tweet, override):
            yield val
    except KeyError as err:
        raise FormattingError('Invalid tag used: ' + err.args[0])
    except ValueError as err:
        raise FormattingError('Unknown value: ' + err.args[0])
